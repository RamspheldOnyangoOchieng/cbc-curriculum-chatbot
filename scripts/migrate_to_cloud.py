import chromadb
import os
from dotenv import load_dotenv
from chromadb.config import Settings

load_dotenv()

def migrate():
    # 1. Local Client
    local_db_path = "./chroma_db"
    print(f"Reading from local DB: {local_db_path}")
    local_client = chromadb.PersistentClient(path=local_db_path)
    
    try:
        local_col = local_client.get_collection("Curriculumnpdfs")
        count = local_col.count()
        print(f"Local collection 'Curriculumnpdfs' has {count} items.")
    except Exception as e:
        print(f"Error accessing local collection: {e}")
        return

    # 2. Cloud Client
    host_url = os.getenv('CHROMA_HOST', 'https://api.trychroma.com')
    api_key = os.getenv('CHROMA_API_KEY')
    tenant = os.getenv('CHROMA_TENANT', 'default_tenant')
    database = os.getenv('CHROMA_DATABASE', 'default_database')

    print(f"Connecting to Cloud: {host_url}")
    print(f"Tenant: {tenant}, DB: {database}")

    # Remove https:// for host argument if needed, or keep it. 
    # Newer HttpClient handles it, but safer to strip protocol if it causes issues, 
    # though usually with ssl=True, host is just the domain.
    # However, let's try the direct settings approach.
    
    # Chroma Cloud Auth (Direct Header)
    cloud_client = chromadb.HttpClient(
        host=host_url.replace("https://", "").replace("http://", ""),
        ssl=True,
        tenant=tenant,
        database=database,
        headers={
            "x-chroma-token": api_key,
            "Content-Type": "application/json"
        }
    )

    # 3. Cloud Collection
    print("Getting/Creating Cloud Collection...")
    cloud_col = cloud_client.get_or_create_collection(
        name="Curriculumnpdfs",
        metadata={"hnsw:space": "cosine"} # Ensure valid distance metric
    )

    # 4. Migrate Data
    print("Fetching local data...")
    # Fetch all data
    data = local_col.get(include=["documents", "metadatas", "embeddings"])
    
    total_items = len(data['ids'])
    if total_items == 0:
        print("No data to migrate.")
        return

    print(f"Starting migration of {total_items} items...")
    
    batch_size = 50
    for i in range(0, total_items, batch_size):
        end = min(i + batch_size, total_items)
        print(f"Upserting batch {i+1}-{end} / {total_items}...")
        
        cloud_col.upsert(
            ids=data['ids'][i:end],
            embeddings=data['embeddings'][i:end], # Use existing embeddings to save cost/time
            documents=data['documents'][i:end],
            metadatas=data['metadatas'][i:end]
        )

    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
