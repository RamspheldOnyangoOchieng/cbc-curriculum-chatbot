
import os
import requests
import json
import sys
from dotenv import load_dotenv

# Set UTF-8 encoding for stdout
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

load_dotenv()

def sync_all_processed_data():
    host = "https://api.trychroma.com"
    api_key = os.getenv('CHROMA_API_KEY')
    tenant = os.getenv('CHROMA_TENANT', 'bb042f26-2c1c-4c18-844b-a569ea3944b4') 
    database = os.getenv('CHROMA_DATABASE', 'cbc-chatbot')
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    
    headers = {
        "x-chroma-token": api_key,
        "Content-Type": "application/json"
    }

    base_url = f"{host}/api/v2/tenants/{tenant}/databases/{database}"
    
    print(f"Connecting to Chroma Cloud v2: {base_url}")
    resp = requests.get(f"{base_url}/collections", headers=headers)
    if resp.status_code != 200:
        print(f"Error listing collections: {resp.status_code} - {resp.text}")
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

    processed_dir = "data/processed"
    if not os.path.exists(processed_dir):
        print(f"Directory not found: {processed_dir}")
        return

    files = [f for f in os.listdir(processed_dir) if f.endswith(".txt")]
    print(f"Found {len(files)} files to sync.")

    for filename in files:
        file_path = os.path.join(processed_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        if not content:
            continue

        print(f"Processing: {filename}...")
        
        chunk = content[:4000] 

        try:
            # TRY ROUTER FIRST
            e_resp = requests.post(
                "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2",
                headers={"Authorization": f"Bearer {hf_token}"},
                json={"inputs": [chunk], "options": {"wait_for_model": True}}
            )
            
            # IF ROUTER FAILS (Deprecated message), TRY DIRECT
            if "longer supported" in e_resp.text:
                 e_resp = requests.post(
                    "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2",
                    headers={"Authorization": f"Bearer {hf_token}"},
                    json={"inputs": [chunk], "options": {"wait_for_model": True}}
                )

            if e_resp.status_code != 200:
                print(f"  FAILED embedding: {e_resp.status_code}")
                continue

            embedding = e_resp.json()[0]

            u_resp = requests.post(
                f"{base_url}/collections/{coll_id}/upsert",
                headers=headers,
                json={
                    "ids": [f"file_{filename}"],
                    "embeddings": [embedding],
                    "documents": [chunk],
                    "metadatas": [{"source": "manual_upload", "filename": filename}]
                }
            )
            
            if u_resp.status_code == 200:
                print(f"  SUCCESS synced.")
            else:
                print(f"  FAILED upsert: {u_resp.status_code}")
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}")

if __name__ == "__main__":
    sync_all_processed_data()
