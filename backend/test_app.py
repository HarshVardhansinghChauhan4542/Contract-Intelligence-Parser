import sys
import os
from fastapi.testclient import TestClient

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

if __name__ == "__main__":
    test_health_check()
    print("Test completed successfully!")
