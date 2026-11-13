import hashlib
import numpy as np
from typing import List
import httpx
from app.core.config import settings
from app.core.logging import logger


class EmbeddingService:
    """
    Modular embedding service supporting OpenAI, Gemini, and deterministic local mock.
    """

    def __init__(self, provider: str = None, dimension: int = None):
        self.provider = provider or settings.DEFAULT_EMBEDDING_PROVIDER
        self.dimension = dimension or settings.EMBEDDING_DIMENSION

    def _generate_mock_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic pseudo-semantic vector using word hash projections.
        Words with shared characters/tokens yield similar vector projections.
        """
        words = text.lower().split()
        vec = np.zeros(self.dimension, dtype=np.float32)

        if not words:
            vec[0] = 1.0
            return vec.tolist()

        for word in words:
            # Hash word and character n-grams
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if (h % 2 == 0) else -1.0
            vec[idx] += sign

            for i in range(len(word) - 2):
                tri = word[i:i+3]
                th = int(hashlib.sha256(tri.encode("utf-8")).hexdigest(), 16)
                tidx = th % self.dimension
                vec[tidx] += 0.5 * (1.0 if (th % 2 == 0) else -1.0)

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            logger.warning("OpenAI API key missing. Falling back to local deterministic embedding.")
            return [self._generate_mock_embedding(t) for t in texts]

        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.EMBEDDING_MODEL,
            "input": texts
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return [item["embedding"] for item in data["data"]]
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}. Falling back to local mock embedding.")
            return [self._generate_mock_embedding(t) for t in texts]

    def _embed_gemini(self, texts: List[str]) -> List[List[float]]:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("Gemini API key missing. Falling back to local deterministic embedding.")
            return [self._generate_mock_embedding(t) for t in texts]

        # Gemini embeddings endpoint
        model = "text-embedding-004"
        results = []
        try:
            with httpx.Client(timeout=30.0) as client:
                for text in texts:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}"
                    payload = {
                        "model": f"models/{model}",
                        "content": {"parts": [{"text": text}]}
                    }
                    res = client.post(url, json=payload)
                    res.raise_for_status()
                    data = res.json()
                    vec = data["embedding"]["values"]
                    # Pad or truncate to self.dimension if needed
                    if len(vec) < self.dimension:
                        vec = vec + [0.0] * (self.dimension - len(vec))
                    elif len(vec) > self.dimension:
                        vec = vec[:self.dimension]
                    results.append(vec)
            return results
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}. Falling back to local mock embedding.")
            return [self._generate_mock_embedding(t) for t in texts]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a list of texts."""
        if not texts:
            return []

        # Check configured provider
        if self.provider == "openai" and settings.OPENAI_API_KEY:
            return self._embed_openai(texts)
        elif self.provider == "gemini" and settings.GEMINI_API_KEY:
            return self._embed_gemini(texts)
        else:
            return [self._generate_mock_embedding(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        """Generates embedding vector for a single query."""
        results = self.embed_texts([query])
        return results[0]


embedding_service = EmbeddingService()

