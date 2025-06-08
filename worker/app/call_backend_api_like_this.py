import requests

BACKEND_API_BASE = "http://backend:8000/api"

def fetch_next_questions(user_id, session_id):
    payload = {
        "user_id": user_id,
        "session_id": session_id
    }
    response = requests.post(f"{BACKEND_API_BASE}/interview/more-questions", json=payload)
    if response.ok:
        print("More questions added.")
    else:
        print(f"Failed to fetch questions: {response.text}")
