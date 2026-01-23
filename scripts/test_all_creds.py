
import os
import sys
import requests
import codecs
from dotenv import load_dotenv

# Force UTF-8 for Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

load_dotenv()

def test_groq():
    api_key = os.getenv("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 5
    }
    print("\n--- TESTING GROQ API KEY ---")
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            print("SUCCESS: Groq API Key is valid.")
        else:
            print(f"FAILED: Groq returned status {resp.status_code}")
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"ERROR: {e}")

def test_huggingface():
    token = os.getenv("HUGGINGFACE_TOKEN")
    model_id = "BAAI/bge-small-en-v1.5"
    url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": ["Testing embedding connection"], "options": {"wait_for_model": True}}
    
    print("\n--- TESTING HUGGINGFACE TOKEN ---")
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            print("SUCCESS: Hugging Face Token is valid.")
        else:
            print(f"FAILED: Hugging Face returned status {resp.status_code}")
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"ERROR: {e}")

def test_chroma():
    api_key = os.getenv('CHROMA_API_KEY')
    tenant = os.getenv('CHROMA_TENANT')
    database = os.getenv('CHROMA_DATABASE')
    url = f"https://api.trychroma.com/api/v2/tenants/{tenant}/databases/{database}/collections"
    headers = {"x-chroma-token": api_key, "Content-Type": "application/json"}
    
    print("\n--- TESTING CHROMA CLOUD API KEY ---")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            print("SUCCESS: Chroma Cloud API Key is valid.")
        else:
            print(f"FAILED: Chroma returned status {resp.status_code}")
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    print("Starting Comprehensive Credential Test...")
    test_groq()
    test_huggingface()
    test_chroma()
