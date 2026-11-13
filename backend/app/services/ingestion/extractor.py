import io
import ipaddress
import socket
from urllib.parse import urlparse
from typing import List, Tuple, Dict, Any
import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader
from app.core.errors import IngestionError, SSRFSecurityError
from app.core.logging import logger

# Private / reserved IPv4 & IPv6 networks for SSRF protection
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def validate_url_safe(url: str) -> None:
    """
    Validates that a URL does not resolve to private, loopback, or cloud-metadata IP addresses (SSRF defense).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFSecurityError(f"Unsupported URL scheme: {parsed.scheme}. Only HTTP and HTTPS are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFSecurityError("Invalid URL: missing hostname.")

    # Check for localhost strings
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
        raise SSRFSecurityError("Access to localhost and internal hostnames is prohibited.")

    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise SSRFSecurityError(f"Could not resolve domain: {hostname}")

    for item in addr_info:
        ip_str = item[4][0]
        ip_obj = ipaddress.ip_address(ip_str)
        for net in BLOCKED_NETWORKS:
            if ip_obj in net:
                logger.warning(f"SSRF Block: Hostname {hostname} resolved to blocked IP {ip_str} in network {net}")
                raise SSRFSecurityError(f"Access to private/internal IP address {ip_str} is prohibited.")


def extract_text_from_pdf(file_bytes: bytes) -> List[Tuple[int, str]]:
    """
    Extracts text page-by-page from a PDF file.
    Returns list of (page_number, text).
    """
    pages = []
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append((page_idx + 1, text))
    except Exception as e:
        logger.error(f"Error extracting PDF: {str(e)}")
        raise IngestionError(f"Failed to parse PDF document: {str(e)}")
    return pages


def extract_text_from_txt(content: str) -> List[Tuple[int, str]]:
    """Extracts text from plaintext, returned as single page."""
    clean = content.strip()
    return [(1, clean)] if clean else []


def extract_text_from_markdown(content: str) -> List[Tuple[int, str]]:
    """Extracts text from markdown file, returned as single page."""
    clean = content.strip()
    return [(1, clean)] if clean else []


def extract_text_from_url(url: str, timeout_seconds: float = 10.0) -> Tuple[str, List[Tuple[int, str]], Dict[str, Any]]:
    """
    Safely fetches and extracts readable text and metadata from a web page.
    Returns (page_title, list_of_pages, metadata_dict).
    """
    validate_url_safe(url)

    headers = {
        "User-Agent": "Cortex-Bot/1.0 (+https://cortex.local/bot; personal knowledge indexing)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        with httpx.Client(follow_redirects=True, max_redirects=3, timeout=timeout_seconds) as client:
            # Re-check each redirect destination if any
            response = client.get(url, headers=headers)
            final_url = str(response.url)
            validate_url_safe(final_url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type and "text/plain" not in content_type and "application/xhtml+xml" not in content_type:
                raise IngestionError(f"Unsupported content type from URL: {content_type}")

            html_text = response.text
    except SSRFSecurityError:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch URL {url}: {str(e)}")
        raise IngestionError(f"Failed to fetch content from URL: {str(e)}")

    soup = BeautifulSoup(html_text, "html.parser")

    # Extract title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)
    if not title:
        title = url

    # Remove non-content elements
    for element in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "aside"]):
        element.decompose()

    # Extract body or main content
    main_content = soup.find("main") or soup.find("article") or soup.find("body") or soup
    text = main_content.get_text(separator="\n", strip=True)

    metadata = {
        "source_url": url,
        "final_url": final_url,
        "status_code": response.status_code,
        "content_type": content_type,
    }

    return title, [(1, text)], metadata
