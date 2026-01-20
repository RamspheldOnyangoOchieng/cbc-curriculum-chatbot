
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def sync_doc(title, content):
    host = os.getenv('CHROMA_HOST', 'https://api.trychroma.com').rstrip('/')
    api_key = os.getenv('CHROMA_API_KEY')
    tenant = os.getenv('CHROMA_TENANT', 'default_tenant')
    database = os.getenv('CHROMA_DATABASE', 'default_database')
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    
    print(f"Syncing to: {host} (Tenant: {tenant}, DB: {database})")
    
    headers = {
        "x-chroma-token": api_key,
        "Content-Type": "application/json"
    }

    # 1. Get or Create Collection using ID-based approach if name fails
    # Standard Chroma Cloud URL structure
    colls_url = f"{host}/api/v1/collections?tenant={tenant}&database={database}"
    try:
        resp = requests.get(colls_url, headers=headers)
        if resp.status_code != 200:
            print(f"Failed to list collections: {resp.status_code} - {resp.text}")
            return
        
        collections = resp.json()
        coll_id = None
        for coll in collections:
            if coll['name'] == "Curriculumnpdfs":
                coll_id = coll['id']
                break
        
        if not coll_id:
            print("Creating collection...")
            create_url = f"{host}/api/v1/collections?tenant={tenant}&database={database}"
            c_resp = requests.post(create_url, headers=headers, json={"name": "Curriculumnpdfs", "metadata": {"hnsw:space": "cosine"}})
            coll_id = c_resp.json()['id']
            
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    # 2. Embed using HF API
    print(f"Embedding {title}...")
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_id}"
    hf_headers = {"Authorization": f"Bearer {hf_token}"}
    
    e_resp = requests.post(api_url, headers=hf_headers, json={"inputs": [content], "options": {"wait_for_model": True}})
    embedding = e_resp.json()[0]

    # 3. Upsert
    print(f"Upserting to collection {coll_id}...")
    upsert_url = f"{host}/api/v1/collections/{coll_id}/upsert?tenant={tenant}&database={database}"
    payload = {
        "ids": [f"cloud_{title}"],
        "embeddings": [embedding],
        "documents": [content],
        "metadatas": [{"source": "manual_push"}]
    }
    
    u_resp = requests.post(upsert_url, headers=headers, json=payload)
    print(f"Final Result: {u_resp.status_code}")
    if u_resp.status_code == 200:
        print("✅ SUCCESS: Data is now in Chroma Cloud!")
    else:
        print(f"❌ FAILED: {u_resp.text}")

if __name__ == "__main__":
    content = """The Kenya Junior Secondary Education Assessment (KJSEA) is the new national assessment replacing the old KCPE system for Grade 9 students under the CBC. 
    Key differences:
    1. System: KCPE was for 8-4-4 system; KJSEA is for the 2-6-3-3-3 CBC system.
    2. Purpose: KCPE was a high-stakes placement exam; KJSEA is a summative assessment component that combines with teacher-based classroom assessments (60% classroom, 40% national exam).
    3. Grade: KCPE was done in Grade 8 (Primary finish); KJSEA is done in Grade 9 (Junior Secondary finish).
    4. Subject Focus: KJSEA focuses on competency and core skills rather than rote memorization.
    """
    sync_doc("KJSEA_Guide", content)
