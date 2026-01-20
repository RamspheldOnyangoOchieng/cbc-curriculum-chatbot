import os
import chromadb
import time
from datasets import load_dataset
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

def ingest_data():
    start_time = time.time()
    
    # 1. Initialize LOCAL Chroma Client
    db_path = "./chroma_db"
    print(f"Connection: Using LOCAL ChromaDB at {db_path}...")
    client = chromadb.PersistentClient(path=db_path)

    # 2. Get or create collection
    collection_name = "Curriculumnpdfs"
    print(f"Collection: Using collection '{collection_name}'")
    
    # We use a default embedding function for faster setup, 
    # but we will manually provide embeddings for better control.
    collection = client.get_or_create_collection(name=collection_name)

    # 3. Load Dataset from Hugging Face
    print("Dataset: Downloading 'JK-TK/webCbdataset'...")
    ds = load_dataset("JK-TK/webCbdataset", split="train")
    
    # 4. Initialize Embedding Model
    print("Model: Loading 'all-MiniLM-L6-v2'... (Fastest for local use)")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # 5. Process and Ingest in smaller batches for responsiveness
    total_records = len(ds)
    print(f"Start: Ingesting {total_records} records locally...")
    
    batch_size = 100
    for i in range(0, total_records, batch_size):
        batch_start = time.time()
        batch = ds[i : i + batch_size]
        
        documents = batch["text"]
        metadatas = [{"source": "huggingface", "index": i + j} for j in range(len(documents))]
        ids = [f"hf_{i + j}" for j in range(len(documents))]

        # Generate embeddings in bulk
        embeddings = model.encode(documents, show_progress_bar=False).tolist()

        # Add to local Chroma
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        batch_end = time.time()
        progress = min(100, ((i + batch_size) / total_records) * 100)
        print(f"Progress: [{progress:.1f}%] Processed {i + len(documents)}/{total_records} records. (Batch: {batch_end - batch_start:.2f}s)")

    end_time = time.time()
    print(f"Done: Local Ingestion complete! Total time: {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    try:
        ingest_data()
    except Exception as e:
        print(f"Error: {e}")
