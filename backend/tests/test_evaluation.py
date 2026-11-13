def test_evaluation_pipeline(client, auth_headers):
    # Check dataset listing
    ds_res = client.get("/api/evaluations/datasets", headers=auth_headers)
    assert ds_res.status_code == 200
    datasets = ds_res.json()
    assert len(datasets) > 0

    # Trigger evaluation run
    payload = {
        "top_k": 3,
        "retrieval_mode": "hybrid"
    }
    run_res = client.post("/api/evaluations/run", json=payload, headers=auth_headers)
    assert run_res.status_code == 201
    run_data = run_res.json()

    # Verify actual calculated metrics
    assert "recall_at_k" in run_data
    assert "mrr" in run_data
    assert "avg_latency_ms" in run_data
    assert run_data["avg_latency_ms"] >= 0
    assert "total_tokens" in run_data
    assert "groundedness_score" in run_data
    assert run_data["sample_count"] > 0
    assert len(run_data["results"]) > 0

    # List past runs
    list_runs = client.get("/api/evaluations", headers=auth_headers)
    assert list_runs.status_code == 200
    assert len(list_runs.json()) > 0
