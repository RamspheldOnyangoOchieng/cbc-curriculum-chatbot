import os
import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

def index_local_docs():
    # 1. Initialize LOCAL Chroma Client
    db_path = "./chroma_db"
    print(f"Connecting to local ChromaDB at {db_path}...")
    client = chromadb.PersistentClient(path=db_path)
    
    # 2. Get or create collection
    collection_name = "Curriculumnpdfs"
    collection = client.get_or_create_collection(name=collection_name)
    
    # 3. Load Embedding Model
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 4. Process text files from data/processed
    processed_dir = "data/processed"
    if not os.path.exists(processed_dir):
        print(f"Directory {processed_dir} not found!")
        return

    for filename in os.listdir(processed_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(processed_dir, filename)
            print(f"Indexing: {filename}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Improved chunking: group lines into segments of ~10 lines
            lines = content.split('\n')
            chunks = []
            chunk_size = 15 # lines per chunk
            for i in range(0, len(lines), chunk_size):
                chunk = "\n".join(lines[i:i + chunk_size]).strip()
                if chunk:
                    chunks = [c for c in chunks if c] + [chunk]
            
            if not chunks:
                continue
                
            ids = [f"local_{filename}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": filename, "type": "local_pdf"} for _ in range(len(chunks))]
            
            # Generate embeddings
            embeddings = model.encode(chunks, show_progress_bar=False).tolist()
            
            # Upsert into Chroma
            collection.upsert(
                ids=ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas
            )
            print(f"Successfully indexed {len(chunks)} chunks from {filename}")

    print("Index update complete!")

if __name__ == "__main__":
    index_local_docs()
