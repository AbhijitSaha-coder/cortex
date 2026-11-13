import io


def test_generate_and_export_report(client, auth_headers):
    # Upload context document first
    doc_text = b"Autonomous research agents leverage chain-of-thought planning, vector memory, and deterministic tool calls to conduct literature synthesis."
    client.post("/api/documents/upload", files={"file": ("agents_paper.txt", io.BytesIO(doc_text), "text/plain")}, headers=auth_headers)

    payload = {
        "research_question": "How do autonomous AI research agents use tools and vector memory?",
        "title": "Comprehensive Survey of Agentic AI",
        "focus_areas": ["Tool Calling", "Vector Memory", "Planning"]
    }
    response = client.post("/api/reports/generate", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()

    assert data["title"] == "Comprehensive Survey of Agentic AI"
    assert "executive_summary" in data
    assert "main_findings" in data
    assert "markdown_content" in data
    assert len(data["markdown_content"]) > 100

    report_id = data["id"]

    # Test get report
    get_res = client.get(f"/api/reports/{report_id}", headers=auth_headers)
    assert get_res.status_code == 200

    # Test export markdown
    export_res = client.get(f"/api/reports/{report_id}/export", headers=auth_headers)
    assert export_res.status_code == 200
    assert "Comprehensive Survey" in export_res.text
    assert "text/markdown" in export_res.headers.get("content-type", "")
