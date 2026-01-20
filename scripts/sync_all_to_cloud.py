
import os
import requests
import json
import sys
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

load_dotenv()

def sync_all():
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
    
    print(f"Connecting to Chroma Cloud v2: {base_url}")
    
    # 1. Get Collection
    resp = requests.get(f"{base_url}/collections", headers=headers)
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

    # 2. Sync all files
    processed_dir = "data/processed"
    files = [f for f in os.listdir(processed_dir) if f.endswith(".txt")]
    print(f"Syncing {len(files)} files...")

    for filename in files:
        file_path = os.path.join(processed_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content: continue
        
        # Limit chunk size for API safety
        chunk = content[:4000] 

        # Embed using the VERIFIED working URL
        e_resp = requests.post(
            "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5",
            headers={"Authorization": f"Bearer {hf_token}"},
            json={"inputs": [chunk], "options": {"wait_for_model": True}}
        )
        
        if e_resp.status_code == 200:
            embedding = e_resp.json()[0]
            # Upsert
            u_resp = requests.post(
                f"{base_url}/collections/{coll_id}/upsert",
                headers=headers,
                json={
                    "ids": [f"file_{filename}"],
                    "embeddings": [embedding],
                    "documents": [chunk],
                    "metadatas": [{"source": filename}]
                }
            )
            print(f"✅ {filename}: Synced.")
        else:
            print(f"❌ {filename}: Embedding failed ({e_resp.status_code})")

if __name__ == "__main__":
    sync_all()
