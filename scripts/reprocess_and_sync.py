
import os
import PyPDF2
import requests
import sys
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

load_dotenv()

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting {pdf_path}: {e}")
    return text

def process_all_pdfs():
    raw_dir = "data/raw"
    processed_dir = "data/processed"
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
    
    pdfs = [f for f in os.listdir(raw_dir) if f.lower().endswith(".pdf")]
    print(f"Found {len(pdfs)} PDFs. Starting extraction...")
    
    for pdf in pdfs:
        txt_name = os.path.splitext(pdf)[0] + ".txt"
        txt_path = os.path.join(processed_dir, txt_name)
        
        # Always re-process as requested
        print(f"Processing {pdf}...")
        content = extract_text_from_pdf(os.path.join(raw_dir, pdf))
        if content.strip():
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Saved to {txt_name}")
        else:
            print(f"  ⚠️ No text found in {pdf}")

def sync_to_cloud():
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
    
    print(f"\nConnecting to Chroma Cloud v2 for Sync...")
    
    # 1. Get/Create Collection
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
    print(f"Syncing {len(files)} files to Cloud...")

    for filename in files:
        file_path = os.path.join(processed_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content: continue
        
        # Chunking for API stability (Chroma and HF have limits)
        # We'll take the first 4000 chars as the primary document snippet
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
            print(f"✅ {filename}: Synced to Cloud.")
        else:
            print(f"❌ {filename}: Embedding failed ({e_resp.status_code})")

if __name__ == "__main__":
    process_all_pdfs()
    sync_to_cloud()
