import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_test():
    print("Starting E2E API Test...")

    email = f"testuser_{int(time.time())}@example.com"
    password = "password123"
    
    print(f"Registering user {email}...")
    res = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email, "password": password, "full_name": "Test E2E"
    })
    token = res.json().get("access_token")
    if not token:
        print("Registration failed:", res.text)
        return
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Creating project...")
    res = requests.post(f"{BASE_URL}/projects", json={
        "name": "E2E Test Project", "description": "Testing the RAG flow"
    }, headers=headers)
    project_id = res.json()["id"]
    
    print("Uploading contract...")
    contract_path = "C:/Users/Administrator/Desktop/clauseiq/sample_contract_a.docx"
    with open(contract_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/contracts?project_id={project_id}", files={"file": f}, headers=headers)
    
    try:
        contract_id = res.json()["id"]
        print(f"Contract uploaded. Status: {res.json()['processing_status']}")
    except KeyError:
        print("Upload failed. Response:")
        print(res.text)
        return
    
    print("Extracting clauses...")
    res = requests.post(f"{BASE_URL}/contracts/{contract_id}/clauses", headers=headers)
    print(res.text)
    
    print("Detecting risks...")
    res = requests.post(f"{BASE_URL}/contracts/{contract_id}/risks", headers=headers)
    print(res.text)
    
    print("Generating summary...")
    res = requests.post(f"{BASE_URL}/contracts/{contract_id}/summary", headers=headers)
    print(res.text)
    
    print("Asking chat...")
    res = requests.post(f"{BASE_URL}/contracts/{contract_id}/chat", json={"question": "What is the term of this agreement?"}, headers=headers)
    print(res.text)

    print("\nE2E API Test Completed Successfully!")

if __name__ == "__main__":
    run_test()
