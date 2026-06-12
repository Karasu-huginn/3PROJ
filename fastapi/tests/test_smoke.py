def test_root_endpoint_responds(client):
    """The app boots and serves the root route under the test harness."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "SCRUM TEAM"}
