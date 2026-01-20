
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def sync_final():
    host = "https://api.trychroma.com"
    api_key = os.getenv('CHROMA_API_KEY')
    tenant = os.getenv('CHROMA_TENANT')
    database = os.getenv('CHROMA_DATABASE')
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    
    headers = {
        "x-chroma-token": api_key,
        "Content-Type": "application/json"
    }

    # 1. Get Collection via v2 API
    base_url = f"{host}/api/v2/tenants/{tenant}/databases/{database}"
    
    print(f"Syncing to Chroma Cloud v2...")
    resp = requests.get(f"{base_url}/collections", headers=headers)
    if resp.status_code != 200:
        print(f"Error listing collections: {resp.status_code}")
        return

    collections = resp.json()
    coll_id = None
    for coll in collections:
        if coll['name'] == "Curriculumnpdfs":
            coll_id = coll['id']
            break
    
    if not coll_id:
        print("Creating collection...")
        resp = requests.post(f"{base_url}/collections", headers=headers, json={"name": "Curriculumnpdfs"})
        coll_id = resp.json()['id']

    # 2. Embed using the confirmed working endpoint
    content = """The Kenya Junior Secondary Education Assessment (KJSEA) is the national assessment replacing the KCPE. 
    Key facts about KJSEA:
    - Replaces KCPE for Grade 9 students.
    - Contributes 40% to the final score (Summative).
    - 60% of the score comes from school-based assessments (SBAs).
    - Grade 10 reporting date is January 12, 2026.
    - It focuses on CBC competencies."""
    
    print("Embedding context...")
    e_resp = requests.post(
        "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2",
        headers={"Authorization": f"Bearer {hf_token}"},
        json={"inputs": [content], "options": {"wait_for_model": True}}
    )
    
    if e_resp.status_code != 200:
        print(f"Embedding failed: {e_resp.text}")
        return

    embedding = e_resp.json()[0]

    # 3. Upsert
    print(f"Upserting to {coll_id}...")
    u_resp = requests.post(
        f"{base_url}/collections/{coll_id}/upsert",
        headers=headers,
        json={
            "ids": ["knowledge_kjsea"],
            "embeddings": [embedding],
            "documents": [content],
            "metadatas": [{"source": "manual_sync"}]
        }
    )
    
    if u_resp.status_code == 200:
        print("✅ SUCCESS! Knowledge is now in Chroma Cloud.")
    else:
        print(f"Upsert failed: {u_resp.text}")

if __name__ == "__main__":
    sync_final()
