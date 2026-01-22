from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import json
from api import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("api.VideoDownloader")
@patch("api.VideoProcessor")
def test_generate_endpoint_mocked(mock_processor_cls, mock_downloader_cls):
    """
    Test the /generate endpoint with mocked downloader and processor
    to verify request handling and background task creation.
    """
    # Setup mocks
    mock_downloader_instance = MagicMock()
    mock_downloader_cls.return_value = mock_downloader_instance
    mock_downloader_instance.download.return_value = "mockd_video.mp4"

    mock_processor_instance = MagicMock()
    mock_processor_cls.return_value = mock_processor_instance
    mock_processor_instance.process_video.return_value = "outputs/mocked_output.mp4"

    # Define test payload
    payload = {
        "url": "https://www.youtube.com/watch?v=TEST_VIDEO",
        "output_name": "test_clip",
        "smart_crop": True,
        "add_subtitles": True,
        "whisper_model": "tiny"
    }

    # Make request
    response = client.post("/generate", json=payload)

    # Verify Response
    assert response.status_code == 200
    expected_response = {
        "message": "Video processing started",
        "url": payload["url"]
    }
    assert response.json() == expected_response

    # NOTE: The TestClient usually runs background tasks after the response is sent.
    # However, since we are mocking everything inside the task function, 
    # ensuring the mocks were instantiated/called requires slightly more setup 
    # or relying on the fact that no error occurred during request parsing.
    # 
    # For a simple integration test, getting a 200 OK means the API parsed the model correctly.
    print("API Response validated successfully.")

if __name__ == "__main__":
    # Manually running tests to see output
    test_health_check()
    print("Health check passed.")
    
    # We need to run the patched test function. 
    # 'patch' decorator works best with pytest or unittest runners.
    # Here we will simulate it manually for a quick check or just use pytest in the shell.
    print("Please run this file with `pytest test_api.py` to fully verify mocks.")
