import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_test():
    print("Starting Detailed E2E API Demo for Existing Account...")

    email = "testuser_1784091422@example.com"
    password = "password123"
    
    print(f"\n1. Logging in as {email}...")
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email, "password": password
    })
    token = res.json().get("access_token")
    if not token:
        print("Login failed:", res.text)
        return
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")
    
    print("\n2. Fetching existing Projects...")
    res = requests.get(f"{BASE_URL}/projects", headers=headers)
    projects = res.json().get("projects", [])
    if not projects:
        print("No projects found for this user.")
        return
    project_id = projects[0]["id"]
    print(f"Found Project ID: {project_id}")
    
    print("\n3. Fetching existing Contracts in the project...")
    res = requests.get(f"{BASE_URL}/contracts?project_id={project_id}", headers=headers)
    contracts = res.json().get("contracts", [])
    if not contracts:
        print("No contracts found in this project.")
        return
    contract_id = contracts[0]["id"]
    print(f"Found Contract ID: {contract_id}")
    
    print("\n4. Running 'Extract Clauses' Feature...")
    res = requests.post(f"{BASE_URL}/contracts/{contract_id}/clauses", headers=headers)
    if res.status_code == 200:
        clauses = res.json().get("clauses", [])
        print(f"Success! Extracted {len(clauses)} clauses. Example:")
        if clauses: print(clauses[0])
    else:
        print("Error during Clause Extraction:", res.text)

    print("\n5. Running 'Detect Risks' Feature...")
    res = requests.post(f"{BASE_URL}/contracts/{contract_id}/risks", headers=headers)
    if res.status_code == 200:
        risks = res.json().get("risks", [])
        print(f"Success! Detected {len(risks)} risks. Example:")
        if risks: print(risks[0])
    else:
        print("Error during Risk Detection:", res.text)

    print("\n6. Running 'Executive Summary' Feature...")
    res = requests.post(f"{BASE_URL}/contracts/{contract_id}/summary", headers=headers)
    if res.status_code == 200:
        print("Success! Executive Summary Generated:")
        print(res.json().get("key_obligations", "No summary output"))
    else:
        print("Error during Executive Summary:", res.text)

    print("\n7. Running 'Chat with Contract' Feature...")
    chat_prompt = "What is the term of this agreement?"
    print(f"Prompt: '{chat_prompt}'")
    res = requests.post(f"{BASE_URL}/contracts/{contract_id}/chat", json={"question": chat_prompt}, headers=headers)
    if res.status_code == 200:
        print("Success! Chat Answer:")
        print(res.json().get("answer", res.text))
    else:
        print("Error during Chat:", res.text)

    print("\n8. Running 'Ask Your Contracts' (Semantic Search) Feature...")
    search_query = "liability"
    print(f"Search Query: '{search_query}'")
    res = requests.post(f"{BASE_URL}/search", json={"project_id": project_id, "query": search_query}, headers=headers)
    if res.status_code == 200:
        results = res.json().get("results", [])
        print(f"Success! Found {len(results)} relevant chunks across contracts. Top hit:")
        if results: print(results[0])
    else:
        print("Error during Search:", res.text)

    print("\nE2E Detailed Demo Completed!")

if __name__ == "__main__":
    run_test()
