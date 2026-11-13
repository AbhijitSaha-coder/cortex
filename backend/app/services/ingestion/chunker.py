import re
from typing import List, Tuple, Dict, Any


class TextChunker:
    """
    Splits text recursively across natural boundaries (paragraphs, sentences, words)
    while preserving page numbers and overlap for RAG context continuity.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursively splits text using the first separator that breaks it into pieces."""
        final_chunks = []
        separator = separators[-1]
        new_separators = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator else list(text)

        good_splits = []
        for s in splits:
            if separator and s:
                good_splits.append(s + separator)
            elif s:
                good_splits.append(s)

        merged = ""
        for s in good_splits:
            if len(merged) + len(s) <= self.chunk_size:
                merged += s
            else:
                if merged:
                    final_chunks.append(merged.strip())
                if len(s) > self.chunk_size and new_separators:
                    sub_chunks = self._split_text(s, new_separators)
                    final_chunks.extend(sub_chunks)
                    merged = ""
                else:
                    merged = s
        if merged.strip():
            final_chunks.append(merged.strip())

        return [c for c in final_chunks if c]

    def chunk_pages(self, pages: List[Tuple[int, str]]) -> List[Dict[str, Any]]:
        """
        Chunks a list of (page_number, text) tuples.
        Returns a list of dicts with chunk_index, content, page_number, and word_count.
        """
        chunks = []
        chunk_idx = 0

        for page_num, page_text in pages:
            # Clean and normalize whitespace
            normalized = re.sub(r"[ \t]+", " ", page_text).strip()
            if not normalized:
                continue

            # Split current page
            page_splits = self._split_text(normalized, self.separators)

            # Apply sliding overlap
            for i, split in enumerate(page_splits):
                chunk_content = split
                if i > 0 and self.chunk_overlap > 0:
                    prev_text = page_splits[i - 1]
                    overlap_prefix = prev_text[-self.chunk_overlap:]
                    # avoid cutting in the middle of a word
                    space_idx = overlap_prefix.find(" ")
                    if space_idx != -1:
                        overlap_prefix = overlap_prefix[space_idx + 1:]
                    chunk_content = overlap_prefix + " " + chunk_content

                chunk_content = chunk_content.strip()
                if not chunk_content:
                    continue

                words = len(chunk_content.split())
                chunks.append({
                    "chunk_index": chunk_idx,
                    "content": chunk_content,
                    "page_number": page_num,
                    "word_count": words,
                })
                chunk_idx += 1

        return chunks

