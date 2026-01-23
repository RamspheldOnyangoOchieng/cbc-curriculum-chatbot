
import os
import sys
import shutil
import tempfile
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import PyPDF2
import trafilatura
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from cbc_bot.engine import CBCEngine

app = FastAPI(title="CBC Chatbot Master API")

# Initialize Master Engine
try:
    master_engine = CBCEngine()
except Exception as e:
    print(f"Failed to load Master Engine: {e}")
    master_engine = None

@app.on_event("startup")
async def startup_event():
    print("🚀 Master Backend is starting up...")
    print(f"CHROMA_HOST: {os.getenv('CHROMA_HOST')}")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

# --- CORE CHAT ENDPOINT ---

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Main Chat Endpoint: Proxies messages to the Master AI Engine.
    Handles semantic retrieval and response synthesis.
    """
    if not master_engine:
        raise HTTPException(status_code=500, detail="AI Engine not initialized correctly.")
    
    try:
        # Convert Pydantic models to dicts for the engine
        message_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
        
        # Get AI response
        response_text = master_engine.get_chat_response(message_dicts)
        
        return {
            "role": "assistant",
            "content": response_text
        }
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- INGESTION LOGIC (Keeping for Admin) ---

class ChromaHTTPClient:
    def __init__(self):
        self.host = os.getenv('CHROMA_HOST', 'https://api.trychroma.com').rstrip('/')
        self.api_key = os.getenv('CHROMA_API_KEY')
        self.tenant = os.getenv('CHROMA_TENANT', 'default_tenant')
        self.database = os.getenv('CHROMA_DATABASE', 'default_database')
        self.headers = {
            "x-chroma-token": self.api_key,
            "Content-Type": "application/json"
        }
        self.base_url = f"{self.host}/api/v2/tenants/{self.tenant}/databases/{self.database}"
    
    def get_collection_id(self, name: str):
        url = f"{self.base_url}/collections"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        for coll in resp.json():
            if coll['name'] == name:
                return coll['id']
        create_resp = requests.post(url, headers=self.headers, json={"name": name})
        create_resp.raise_for_status()
        return create_resp.json()['id']

    def upsert(self, collection_name: str, ids: List[str], embeddings: List[List[float]], 
               documents: List[str], metadatas: List[dict]):
        coll_id = self.get_collection_id(collection_name)
        url = f"{self.base_url}/collections/{coll_id}/upsert"
        payload = {
            "ids": ids,
            "embeddings": embeddings,
            "documents": documents,
            "metadatas": metadatas
        }
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

def get_embeddings(texts: List[str]) -> List[List[float]]:
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    model_id = "BAAI/bge-small-en-v1.5"
    api_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    try:
        response = requests.post(api_url, headers=headers, json={"inputs": texts, "options": {"wait_for_model": True}})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding API failed: {str(e)}")

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted: text += extracted + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def chunk_text(text: str, chunk_size_lines: int = 15) -> List[str]:
    lines = text.split('\n')
    chunks = []
    for i in range(0, len(lines), chunk_size_lines):
        chunk = "\n".join(lines[i:i + chunk_size_lines]).strip()
        if chunk: chunks.append(chunk)
    return chunks

def process_and_index_file(file_path: str, filename: str):
    try:
        if filename.lower().endswith('.pdf'):
            content = extract_text_from_pdf(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        if not content.strip(): return
        chunks = chunk_text(content)
        embeddings = get_embeddings(chunks)
        chroma_client = ChromaHTTPClient()
        ids = [f"cloud_{filename}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": filename, "type": "cloud_upload"} for _ in range(len(chunks))]
        chroma_client.upsert("Curriculumnpdfs", ids, embeddings, chunks, metadatas)
    except Exception as e:
        print(f"Error processing {filename}: {e}")

@app.get("/")
def health_check():
    return {"status": "ok", "service": "CBC Master AI Backend"}

@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        if background_tasks:
            background_tasks.add_task(process_and_cleanup, tmp_path, file.filename)
        else:
            process_and_cleanup(tmp_path, file.filename)
        return {"success": True, "message": f"File {file.filename} queued."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_and_cleanup(tmp_path: str, filename: str):
    try:
        process_and_index_file(tmp_path, filename)
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)

@app.post("/ingest-url")
async def ingest_url(data: dict, background_tasks: BackgroundTasks = None):
    """
    Scrape a URL and index its content.
    Expects json: {"url": "https://example.com"}
    """
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")
        
    if background_tasks:
        background_tasks.add_task(process_url, url)
    else:
        process_url(url)
        
    return {"success": True, "message": f"URL {url} queued for scraping and indexing."}

def process_url(url: str):
    try:
        print(f"Scraping URL: {url}")
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            print(f"Failed to fetch URL: {url}")
            return
            
        content = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
        if not content:
            print(f"Failed to extract content from: {url}")
            return
            
        # Aligned Chunking and Indexing
        chunks = chunk_text(content)
        embeddings = get_embeddings(chunks)
        
        chroma_client = ChromaHTTPClient()
        # Use safe characters for IDs
        safe_url = "".join([c if c.isalnum() else "_" for c in url])[:100]
        ids = [f"url_{safe_url}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": url, "type": "url_ingest"} for _ in range(len(chunks))]
        
        chroma_client.upsert("Curriculumnpdfs", ids, embeddings, chunks, metadatas)
        print(f"Successfully indexed {len(chunks)} chunks from URL: {url}")
        
    except Exception as e:
        print(f"Error processing URL {url}: {e}")

@app.post("/ingest-text")
async def ingest_text(data: dict):
    """
    Ingest raw text (e.g. from copy-paste).
    Expects json: {"title": "foo", "text": "bar"}
    """
    title = data.get("title", "Untitled")
    text = data.get("text", "")
    
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
        
    # Process
    try:
        chunks = chunk_text(text)
        embeddings = get_embeddings(chunks)
        
        chroma_client = ChromaHTTPClient()
        
        ids = [f"cloud_text_{title}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": title, "type": "cloud_text"} for _ in range(len(chunks))]
        
        chroma_client.upsert(
            collection_name="Curriculumnpdfs",
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        return {"success": True, "indexed_chunks": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
