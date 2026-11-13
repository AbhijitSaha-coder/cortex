import pytest
from app.services.ingestion.chunker import TextChunker
from app.services.ingestion.extractor import validate_url_safe
from app.core.errors import SSRFSecurityError


def test_chunker_basic_and_overlap():
    chunker = TextChunker(chunk_size=100, chunk_overlap=25)
    pages = [(1, "Paragraph one is introductory.\n\nParagraph two discusses detailed findings.\n\nParagraph three concludes the paper.")]
    chunks = chunker.chunk_pages(pages)

    assert len(chunks) >= 2
    for c in chunks:
        assert c["page_number"] == 1
        assert "content" in c
        assert c["word_count"] > 0
    # Sequential chunk indices
    assert [c["chunk_index"] for c in chunks] == list(range(len(chunks)))


def test_ssrf_blocks_private_and_loopback_ips():
    blocked_urls = [
        "http://localhost:8000/secret",
        "http://127.0.0.1/admin",
        "http://10.0.0.5/internal",
        "http://172.16.0.10/config",
        "http://192.168.1.1/router",
        "http://169.254.169.254/latest/meta-data/",
        "ftp://example.com/file.txt",
    ]

    for url in blocked_urls:
        with pytest.raises(SSRFSecurityError):
            validate_url_safe(url)


def test_duplicate_detection_hash():
    import hashlib
    data1 = b"Identical paper content for duplicate detection testing."
    data2 = b"Identical paper content for duplicate detection testing."
    data3 = b"Different content altogether."

    h1 = hashlib.sha256(data1).hexdigest()
    h2 = hashlib.sha256(data2).hexdigest()
    h3 = hashlib.sha256(data3).hexdigest()

    assert h1 == h2
    assert h1 != h3

