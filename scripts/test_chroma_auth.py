
import os
import requests
import sys
import codecs
from dotenv import load_dotenv

# Force UTF-8 for Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

load_dotenv()

def test_chroma_connection():
    api_key = os.getenv('CHROMA_API_KEY')
    tenant = os.getenv('CHROMA_TENANT')
    database = os.getenv('CHROMA_DATABASE')
    host = "https://api.trychroma.com"
    
    print("--- CHROMA CLOUD CONNECTION TEST ---")
    
    headers = {
        "x-chroma-token": api_key,
        "Content-Type": "application/json"
    }
    
    url = f"{host}/api/v2/tenants/{tenant}/databases/{database}/collections"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            collections = response.json()
            print("SUCCESS: Connection to Chroma Cloud established.")
            print(f"Tenant: {tenant}")
            print(f"Database: {database}")
            print(f"Total Collections Found: {len(collections)}")
            for c in collections:
                print(f" - Collection: {c['name']}")
        else:
            print(f"FAILED: Status {response.status_code}")
            print(f"Response Body: {response.text}")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_chroma_connection()
