
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def sync_v2_final():
    host = "https://api.trychroma.com"
    api_key = os.getenv('CHROMA_API_KEY')
    tenant = os.getenv('CHROMA_TENANT')
    database = os.getenv('CHROMA_DATABASE')
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    
    headers = {
        "x-chroma-token": api_key,
        "Content-Type": "application/json"
    }

    base_url = f"{host}/api/v2/tenants/{tenant}/databases/{database}"
    print(f"Checking collection on v2 API: {base_url}")
    
    resp = requests.get(f"{base_url}/collections", headers=headers)
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
        return

    collections = resp.json()
    coll_id = None
    for coll in collections:
        if coll['name'] == "Curriculumnpdfs":
            coll_id = coll['id']
            break
    
    if not coll_id:
        print("Creating collection on v2...")
        resp = requests.post(f"{base_url}/collections", headers=headers, json={"name": "Curriculumnpdfs"})
        coll_id = resp.json()['id']

    # 2. Embed
    content = """The Kenya Junior Secondary Education Assessment (KJSEA) is the national assessment replacing the KCPE. 
    It is done at Grade 9. It contributes 40% to the final score, while 60% comes from school-based assessments.
    Grade 10 reporting is January 12, 2026."""
    
    print("Embedding question...")
    # UPDATED URL: Using router.huggingface.co as requested by HF API
    e_resp = requests.post(
        "https://router.huggingface.co/sentence-transformers/all-MiniLM-L6-v2",
        headers={"Authorization": f"Bearer {hf_token}"},
        json={"inputs": [content], "options": {"wait_for_model": True}}
    )
    
    e_data = e_resp.json()
    if isinstance(e_data, list):
        embedding = e_data[0]
    else:
        print(f"Embedding error: {e_data}")
        return

    # 3. Upsert
    print(f"Upserting to {coll_id}...")
    u_resp = requests.post(
        f"{base_url}/collections/{coll_id}/upsert",
        headers=headers,
        json={
            "ids": ["manual_v2_kjsea"],
            "embeddings": [embedding],
            "documents": [content],
            "metadatas": [{"source": "manual_v2"}]
        }
    )
    print(f"Result: {u_resp.status_code}")
    if u_resp.status_code == 200:
        print("✅ SUCCESS!")
    else:
        print(f"Upsert error: {u_resp.text}")

if __name__ == "__main__":
    sync_v2_final()
