
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def sync_target_file():
    file_path = Path("data/processed/Grade_10_Placement_Crisis_Deep_Final.txt")
    if not file_path.exists():
        print("File not found.")
        return

    host = os.getenv('CHROMA_HOST', 'https://api.trychroma.com')
    api_key = os.getenv('CHROMA_API_KEY')
    tenant = os.getenv('CHROMA_TENANT')
    database = os.getenv('CHROMA_DATABASE')
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    
    headers = {
        "x-chroma-token": api_key,
        "Content-Type": "application/json"
    }
    
    base_url = f"{host}/api/v2/tenants/{tenant}/databases/{database}"
    
    # Get collection ID
    resp = requests.get(f"{base_url}/collections", headers=headers)
    coll_id = [c['id'] for c in resp.json() if c['name'] == "Curriculumnpdfs"][0]

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # Split into chunks of 3000 chars
    chunks = [content[i:i+3000] for i in range(0, len(content), 3000)]
    
    for i, chunk in enumerate(chunks):
        # Embed
        e_resp = requests.post(
            "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5",
            headers={"Authorization": f"Bearer {hf_token}"},
            json={"inputs": [chunk], "options": {"wait_for_model": True}}
        )
        embedding = e_resp.json()[0]
        
        # Upsert
        requests.post(
            f"{base_url}/collections/{coll_id}/upsert",
            headers=headers,
            json={
                "ids": [f"deep_opinion_{i}"],
                "embeddings": [embedding],
                "documents": [chunk],
                "metadatas": [{"source": "Grade_10_Placement_Crisis_Deep_Final.txt"}]
            }
        )
    print(f"✅ Successfully synced {len(chunks)} chunks from the Deep Opinion article.")

if __name__ == "__main__":
    sync_target_file()
