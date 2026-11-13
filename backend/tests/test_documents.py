import io


def test_upload_text_document(client, auth_headers):
    file_content = b"Cortex is an AI research assistant capable of processing papers, reports, and data."
    files = {"file": ("test_research.txt", io.BytesIO(file_content), "text/plain")}
    response = client.post("/api/documents/upload", files=files, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Research"
    assert data["file_type"] == "txt"
    assert data["status"] in ("completed", "processing", "queued")


def test_upload_markdown_document(client, auth_headers):
    md_content = b"""# Machine Learning Architecture
## Overview
Transformer models rely heavily on self-attention mechanisms to process sequential information.
"""
    files = {"file": ("transformers.md", io.BytesIO(md_content), "text/markdown")}
    response = client.post("/api/documents/upload", files=files, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["file_type"] == "md"
    assert data["chunk_count"] > 0


def test_document_user_isolation(client, auth_headers, second_auth_headers):
    # User 1 uploads document
    files = {"file": ("private_notes.txt", io.BytesIO(b"Confidential user 1 notes"), "text/plain")}
    upload_res = client.post("/api/documents/upload", files=files, headers=auth_headers)
    doc_id = upload_res.json()["id"]

    # User 1 can see it
    res1 = client.get(f"/api/documents/{doc_id}", headers=auth_headers)
    assert res1.status_code == 200

    # User 2 CANNOT see it (returns 404)
    res2 = client.get(f"/api/documents/{doc_id}", headers=second_auth_headers)
    assert res2.status_code == 404

    # User 2 list documents should be empty
    list_res = client.get("/api/documents", headers=second_auth_headers)
    assert not any(d["id"] == doc_id for d in list_res.json())


def test_delete_document_cascade(client, auth_headers):
    files = {"file": ("to_delete.txt", io.BytesIO(b"Temporary data to delete"), "text/plain")}
    upload_res = client.post("/api/documents/upload", files=files, headers=auth_headers)
    doc_id = upload_res.json()["id"]

    del_res = client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # Now verify it is gone
    check_res = client.get(f"/api/documents/{doc_id}", headers=auth_headers)
    assert check_res.status_code == 404


def test_upload_invalid_extension(client, auth_headers):
    files = {"file": ("malicious.exe", io.BytesIO(b"echo unsafe"), "application/octet-stream")}
    response = client.post("/api/documents/upload", files=files, headers=auth_headers)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

