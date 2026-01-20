
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def get_embeddings(texts):
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_id}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    response = requests.post(api_url, headers=headers, json={"inputs": texts, "options": {"wait_for_model": True}})
    response.raise_for_status()
    return response.json()

def sync_doc(title, content):
    host = os.getenv('CHROMA_HOST').rstrip('/')
    api_key = os.getenv('CHROMA_API_KEY')
    tenant = os.getenv('CHROMA_TENANT', 'default_tenant')
    database = os.getenv('CHROMA_DATABASE', 'default_database')
    
    headers = {
        "x-chroma-token": api_key,
        "Content-Type": "application/json"
    }
    
    # 1. List collections and find the one named Curriculumnpdfs
    url = f"{host}/api/v1/collections?tenant={tenant}&database={database}"
    resp = requests.get(url, headers=headers)
    print(f"Collections list status: {resp.status_code}")
    
    collections = resp.json()
    coll_id = None
    for coll in collections:
        if coll['name'] == "Curriculumnpdfs":
            coll_id = coll['id']
            break
            
    if not coll_id:
        print("Collection 'Curriculumnpdfs' not found. Creating it...")
        create_url = f"{host}/api/v1/collections?tenant={tenant}&database={database}"
        c_resp = requests.post(create_url, headers=headers, json={"name": "Curriculumnpdfs"})
        print(f"Create response: {c_resp.status_code}")
        coll_id = c_resp.json()['id']
    
    print(f"Using Collection ID: {coll_id}")
    
    # 2. Embed
    print(f"Embedding: {title}...")
    embedding = get_embeddings([content])[0]
    
    # 3. Upsert
    upsert_url = f"{host}/api/v1/collections/{coll_id}/upsert?tenant={tenant}&database={database}"
    payload = {
        "ids": [f"manual_{title}"],
        "embeddings": [embedding],
        "documents": [content],
        "metadatas": [{"source": "manual_sync", "title": title}]
    }
    
    u_resp = requests.post(upsert_url, headers=headers, json=payload)
    print(f"Result for {title}: {u_resp.status_code}")
    if u_resp.status_code != 200:
        print(f"Error detail: {u_resp.text}")

if __name__ == "__main__":
    file_path = "data/processed/How KJSEA Differs From the Old KCPE System.txt"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        sync_doc("KJSEA_Guide", content)
    else:
        print(f"File not found: {file_path}")
