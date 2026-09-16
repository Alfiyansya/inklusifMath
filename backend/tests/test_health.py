"""
Basic health check test to verify the API is running.
"""


async def test_health_check(client):
    """Test that the health endpoint returns 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
