
import os
import sys
import shutil
import tempfile
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
# from sentence_transformers import SentenceTransformer (Removed to save memory)
import PyPDF2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

app = FastAPI(title="CBC Chatbot Admin API")

@app.on_event("startup")
async def startup_event():
    print("🚀 Backend is starting up...")
    print(f"CHROMA_HOST: {os.getenv('CHROMA_HOST')}")
    if not os.getenv("HUGGINGFACE_TOKEN"):
        print("⚠️ WARNING: HUGGINGFACE_TOKEN is not set!")

# Allow CORS (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CHROMA HTTP CLIENT ---
class ChromaHTTPClient:
    def __init__(self):
        self.host = os.getenv('CHROMA_HOST', 'https://api.trychroma.com')
        self.api_key = os.getenv('CHROMA_API_KEY')
        self.tenant = os.getenv('CHROMA_TENANT', 'default_tenant')
        self.database = os.getenv('CHROMA_DATABASE', 'default_database')
        self.headers = {
            "x-chroma-token": self.api_key,
            "Content-Type": "application/json"
        }
        self.base_url = f"{self.host}/api/v1"
    
    def upsert(self, collection_name: str, ids: List[str], embeddings: List[List[float]], 
               documents: List[str], metadatas: List[dict]):
        """Upsert documents to a collection"""
        url = f"{self.base_url}/collections/{collection_name}/upsert"
        payload = {
            "ids": ids,
            "embeddings": embeddings,
            "documents": documents,
            "metadatas": metadatas
        }
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

# --- EMBEDDING HELPER (HF API to save memory on Render) ---
def get_embeddings(texts: List[str]) -> List[List[float]]:
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    try:
        response = requests.post(api_url, headers=headers, json={"inputs": texts, "options": {"wait_for_model": True}})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Embedding error: {e}")
        # Fallback error handling
        raise HTTPException(status_code=500, detail=f"Embedding API failed: {str(e)}")

# --- HELPERS ---
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
    return text

def chunk_text(text: str, chunk_size_lines: int = 15) -> List[str]:
    lines = text.split('\n')
    chunks = []
    for i in range(0, len(lines), chunk_size_lines):
        chunk = "\n".join(lines[i:i + chunk_size_lines]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks

def process_and_index_file(file_path: str, filename: str):
    """
    Extracts text, chunks it, embeds it, and upserts to Chroma Cloud.
    """
    try:
        # 1. Extract
        if filename.lower().endswith('.pdf'):
            content = extract_text_from_pdf(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        if not content.strip():
            print(f"No content extracted from {filename}")
            return

        # 2. Chunk
        chunks = chunk_text(content)
        if not chunks:
            return

        # 3. Embed (Using HF API)
        embeddings = get_embeddings(chunks)

        # 4. Upsert via HTTP
        chroma_client = ChromaHTTPClient()
        
        ids = [f"cloud_{filename}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": filename, "type": "cloud_upload"} for _ in range(len(chunks))]
        
        chroma_client.upsert(
            collection_name="Curriculumnpdfs",
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        print(f"Successfully indexed {len(chunks)} chunks from {filename}")
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")


# --- API ENDPOINTS ---

@app.get("/")
def health_check():
    print("✅ Health check hit!")
    return {"status": "ok", "service": "CBC Chatbot Backend"}

@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Receives a file, saves it temporarily, and processes it in the background.
    """
    try:
        # Create temp file
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        # Run processing immediately (awaiting it here for simplicity in feedback, 
        # but could use background_tasks if timeout is concern on Render free tier)
        # For better UX, we'll return immediately and process in BG.
        
        if background_tasks:
            background_tasks.add_task(process_and_cleanup, tmp_path, file.filename)
        else:
            # Fallback if no BG tasks (shouldn't happen in FastAPI)
            process_and_cleanup(tmp_path, file.filename)
            
        return {"success": True, "message": f"File {file.filename} queued for ingestion."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_and_cleanup(tmp_path: str, filename: str):
    try:
        process_and_index_file(tmp_path, filename)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

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
    # Listen on port defined by PORT env var (Render default) or 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
