
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def master_reset():
    host = os.getenv('CHROMA_HOST', 'https://api.trychroma.com').rstrip('/')
    api_key = os.getenv('CHROMA_API_KEY')
    tenant = os.getenv('CHROMA_TENANT')
    database = os.getenv('CHROMA_DATABASE')
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    
    headers = {"x-chroma-token": api_key, "Content-Type": "application/json"}
    base_url = f"{host}/api/v2/tenants/{tenant}/databases/{database}"
    collection_name = "Curriculumnpdfs"

    print(f"--- DATABASE MASTER RESET ---")
    
    # 1. DELETE OLD COLLECTION
    print(f"Deleting collection: {collection_name}...")
    try:
        resp = requests.get(f"{base_url}/collections", headers=headers)
        collections = resp.json()
        for coll in collections:
            if coll['name'] == collection_name:
                requests.delete(f"{base_url}/collections/{coll['id']}", headers=headers)
                print("✅ Old collection wiped.")
                break
    except Exception as e:
        print(f"Delete failed (likely already gone): {e}")

    # 2. CREATE FRESH COLLECTION
    print(f"Creating fresh collection: {collection_name}...")
    resp = requests.post(f"{base_url}/collections", headers=headers, json={"name": collection_name})
    
    if resp.status_code not in [200, 201]:
        print(f"ERROR: Collection creation failed (Status {resp.status_code}): {resp.text}")
        # Try one more time to just GET the ID in case it was created but timed out
        resp = requests.get(f"{base_url}/collections", headers=headers)
        for coll in resp.json():
            if coll['name'] == collection_name:
                coll_id = coll['id']
                print(f"Found existing collection ID instead: {coll_id}")
                break
        else:
            return # Exit if we truly can't get an ID
    else:
        coll_id = resp.json()['id']
        print(f"✅ New Collection ID: {coll_id}")

    # 3. RE-INDEX ALL PROCESSED DATA
    processed_files = list(Path("data/processed").glob("*.txt"))
    print(f"Indexing {len(processed_files)} high-quality files...")

    for file_path in processed_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if len(content) < 50: continue

        # Chunking: 1500 chars with 200 char overlap for better context retention
        chunks = []
        step = 1300
        for i in range(0, len(content), step):
            chunks.append(content[i:i+1500])

        print(f" -> {file_path.name} ({len(chunks)} chunks)")

        # Embed using the ALIGNED format (no prefix)
        e_resp = requests.post(
            "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5",
            headers={"Authorization": f"Bearer {hf_token}"},
            json={"inputs": chunks, "options": {"wait_for_model": True}}
        )
        embeddings = e_resp.json()

        # Uppert
        requests.post(
            f"{base_url}/collections/{coll_id}/upsert",
            headers=headers,
            json={
                "ids": [f"aligned_{file_path.stem}_{i}" for i in range(len(chunks))],
                "embeddings": embeddings,
                "documents": chunks,
                "metadatas": [{"source": file_path.name} for _ in range(len(chunks))]
            }
        )
    
    print("\n✅ DATABASE RESET COMPLETE: All context is now aligned and searchable.")

if __name__ == "__main__":
    master_reset()
