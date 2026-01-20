
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_chroma():
    host = os.getenv('CHROMA_HOST', 'https://api.trychroma.com')
    api_key = os.getenv('CHROMA_API_KEY')
    tenant = os.getenv('CHROMA_TENANT')
    database = os.getenv('CHROMA_DATABASE')
    
    print(f"Checking Chroma Cloud at: {host}")
    print(f"Tenant: {tenant}")
    print(f"Database: {database}")
    
    headers = {
        "x-chroma-token": api_key,
        "Content-Type": "application/json"
    }
    
    # 1. Check collections
    try:
        url = f"{host}/api/v1/collections?tenant={tenant}&database={database}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        collections = response.json()
        print(f"\nFound {len(collections)} collections:")
        for coll in collections:
            print(f"- {coll['name']} (ID: {coll['id']})")
            
            # 2. Check document count for Curriculumnpdfs
            if coll['name'] == "Curriculumnpdfs":
                count_url = f"{host}/api/v1/collections/{coll['id']}/count?tenant={tenant}&database={database}"
                count_resp = requests.get(count_url, headers=headers)
                print(f"  Count: {count_resp.json()}")
                
                # 3. Peek at some documents
                peek_url = f"{host}/api/v1/collections/{coll['id']}/get?tenant={tenant}&database={database}"
                peek_resp = requests.post(peek_url, headers=headers, json={"limit": 2})
                peek_data = peek_resp.json()
                if peek_data.get('documents'):
                    print(f"  Sample Doc: {peek_data['documents'][0][:100]}...")
                else:
                    print("  ⚠️ No documents found in this collection!")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_chroma()
