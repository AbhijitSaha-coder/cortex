import io
from app.services.retrieval.hybrid_search import HybridSearchEngine
from app.services.retrieval.reranker import CrossEncoderReranker


def test_hybrid_search_and_rrf(client, auth_headers, db, test_user):
    # Upload sample knowledge
    doc1_text = b"PostgreSQL with pgvector provides high dimensional vector search for semantic retrieval in RAG."
    doc2_text = b"Reciprocal Rank Fusion RRF combines scores from keyword BM25 and semantic dense embeddings."
    
    client.post("/api/documents/upload", files={"file": ("pgvector.txt", io.BytesIO(doc1_text), "text/plain")}, headers=auth_headers)
    client.post("/api/documents/upload", files={"file": ("rrf_guide.txt", io.BytesIO(doc2_text), "text/plain")}, headers=auth_headers)

    engine = HybridSearchEngine(db)

    # 1. Semantic Search
    sem_res = engine.search(query="vector search pgvector", user_id=test_user.id, mode="semantic", top_k=3)
    assert len(sem_res["results"]) > 0

    # 2. Keyword Search
    kw_res = engine.search(query="Reciprocal Rank Fusion", user_id=test_user.id, mode="keyword", top_k=3)
    assert len(kw_res["results"]) > 0

    # 3. Hybrid Search
    hybrid_res = engine.search(query="RRF hybrid retrieval", user_id=test_user.id, mode="hybrid", top_k=3)
    assert len(hybrid_res["results"]) > 0
    assert hybrid_res["mode"] == "hybrid"


def test_reranker_relevance_boost():
    reranker = CrossEncoderReranker()
    query = "quantum computing error mitigation"
    chunks = [
        {"content": "A treatise on botany and chlorophyll synthesis.", "document_title": "Botany", "score": 0.6},
        {"content": "Techniques for quantum computing error mitigation using zero noise extrapolation.", "document_title": "Quantum Physics", "score": 0.55},
    ]

    reranked = reranker.rerank(query, chunks, top_k=2)
    # The quantum paper should be ranked #1 after reranking due to exact phrase & term coverage
    assert "Quantum" in reranked[0]["document_title"]
    assert reranked[0]["score"] > reranked[1]["score"]


def test_search_endpoint(client, auth_headers):
    payload = {
        "query": "system architecture",
        "mode": "hybrid",
        "top_k": 3,
        "rerank": True
    }
    response = client.post("/api/search", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "execution_time_ms" in data
