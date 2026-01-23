"""
CBC Web Sources Ingestion Script
================================
Harvests content from various web sources including:
- News articles (educationnews.co.ke, kenyans.co.ke, etc.)
- Google Drive/Share links (PDFs, Documents)
- Facebook posts
- KICD, KNEC and other education portals

Then processes and syncs to Chroma Cloud.
"""

import os
import sys
import re
import json
import time
import hashlib
import requests
import urllib3
from pathlib import Path

# Disable SSL warnings for cases where we bypass verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Force UTF-8 for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

# All the source URLs to harvest
SOURCE_URLS = [
    # News Articles
    ("article", "https://educationnews.co.ke/government-unveils-proposals-to-restructure-cbc-for-junior-andsenior-schools-2/"),
    ("article", "https://www.kenyans.co.ke/news/119387-education-ministry-rejects-60000-student-transfer-requests-over-school-capacity"),
    ("article", "https://thekenyatimes.com/education/students-requirements-admission/"),
    
    # Google Share Links (these require special handling)
    ("google_share", "https://share.google/ysiS84EjNPpW9qtVr"),  # KEMIS System
    ("google_share", "https://share.google/PcEId2FS9sTjhEd1s"),  # 36 Best Career Paths
    ("google_share", "https://share.google/Y3oFHuGLKN7ILbzDj"),  # Sports And Recreation
    ("google_share", "https://share.google/RPxQqmVWwcAPWyqoF"),  # History And Citizenship Careers
    ("google_share", "https://share.google/lhWOkHDjYvXnGCDjd"),  # CBC Senior School Subject Combinations
    ("google_share", "https://share.google/Zqi2vKPgrN8LBpTNX"),  # Subject Combinations PDF 
    ("google_share", "https://share.google/rUIoMFwWPM5GDhvLt"),  # 36 Best Career Paths Alt
    ("google_share", "https://share.google/Mw1saVG0j0sgD27fO"),  # PS Bitok Placement
    ("google_share", "https://share.google/tApOoaRWB5ecNXADM"),  # KNEC Portals
    ("google_share", "https://share.google/Hpk3J1RZPmm595Iym"),  # 2026 Registration Circular
    ("google_share", "https://share.google/I84rzVCWqx1FncR9O"),  # Digital Content Kenya Education Cloud
    ("google_share", "https://share.google/qM3bMUxegFZoVWFQ9"),  # CBC AI App
    ("google_share", "https://share.google/zMKYKGMhqWTFaHbF9"),  # KICD
    
    # Facebook (requires browser automation)
    ("facebook", "https://m.facebook.com/story.php?story_fbid=pfbid0k9NCbgaQ81DTykYDUr1PqT4UVvjwnJ2LjemEVwLYx8VzXTW2y4LKUG9zHuFrT6X4l&id=100004655256269"),
]

RAW_DIR = Path("data/raw_web")
PROCESSED_DIR = Path("data/processed")
METADATA_FILE = Path("data/web_sources_metadata.json")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def sanitize_filename(text, max_length=80):
    """Create a safe filename from text."""
    # Remove special characters
    safe = re.sub(r'[^\w\s-]', '', text)
    safe = re.sub(r'[-\s]+', '_', safe).strip('_')
    return safe[:max_length]

def generate_id(url):
    """Generate a unique ID for a URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]

def load_metadata():
    """Load existing metadata."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"sources": {}, "last_updated": None}

def save_metadata(metadata):
    """Save metadata."""
    metadata["last_updated"] = datetime.now().isoformat()
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

# ============================================================================
# CONTENT EXTRACTORS
# ============================================================================

def extract_article_content(url):
    """
    Extract main content from news articles using trafilatura or fallback.
    """
    try:
        # Try trafilatura first (best quality)
        try:
            import trafilatura
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
                if text and len(text) > 200:
                    return {"success": True, "content": text, "method": "trafilatura"}
        except ImportError:
            print("  -> trafilatura not installed, using fallback...")
        
        # Fallback to BeautifulSoup
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.SSLError:
            print(f"  -> SSL Error for {url}. Retrying without verification...")
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
        except Exception:
            # Try without verify as last resort for any connection error that might be SSL/Cert related
            print(f"  -> Connection Error for {url}. Retrying without verification...")
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'iframe']):
            tag.decompose()
        
        # Try to find main content area
        article = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'content|article|post'))
        
        if article:
            text = article.get_text(separator='\n', strip=True)
        else:
            # Get body text
            text = soup.body.get_text(separator='\n', strip=True) if soup.body else ""
        
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        # Get title
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else ""
        
        if text and len(text) > 100:
            full_content = f"# {title_text}\n\nSource: {url}\n\n{text}"
            return {"success": True, "content": full_content, "title": title_text, "method": "beautifulsoup"}
        
        return {"success": False, "error": "Could not extract meaningful content"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_google_share_content(url):
    """
    Handle Google Share links - these often redirect to Drive or other Google services.
    We'll try to resolve and download the content.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # Follow redirects to get the final URL
        session = requests.Session()
        try:
            response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
            print(f"  -> SSL/Connection Error for {url}. Retrying without verification...")
            response = session.get(url, headers=headers, timeout=30, allow_redirects=True, verify=False)
        
        final_url = response.url
        
        print(f"  -> Resolved to: {final_url}")
        
        # Check if it's a Google Drive file
        if 'drive.google.com' in final_url or 'docs.google.com' in final_url:
            # Extract file ID
            file_id = None
            patterns = [
                r'/d/([a-zA-Z0-9_-]+)',
                r'id=([a-zA-Z0-9_-]+)',
                r'/file/d/([a-zA-Z0-9_-]+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, final_url)
                if match:
                    file_id = match.group(1)
                    break
            
            if file_id:
                # Try to download using gdown
                try:
                    import gdown
                    output_path = RAW_DIR / f"gdrive_{file_id}.pdf"
                    gdown.download(f"https://drive.google.com/uc?id={file_id}", str(output_path), quiet=False)
                    if output_path.exists():
                        return {
                            "success": True, 
                            "type": "pdf_download",
                            "file_path": str(output_path),
                            "method": "gdown"
                        }
                except Exception as e:
                    print(f"  -> gdown failed: {e}")
        
        # If not a drive file, try to extract content from the page
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove scripts and styles
        for tag in soup(['script', 'style']):
            tag.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        if len(text) > 200:
            return {"success": True, "content": text, "method": "html_extract", "final_url": final_url}
        
        return {"success": False, "error": "Could not extract content", "final_url": final_url, "needs_browser": True}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_facebook_content(url):
    """
    Facebook requires JavaScript rendering - mark for browser processing.
    """
    return {
        "success": False, 
        "error": "Facebook requires browser automation",
        "needs_browser": True,
        "url": url
    }

# ============================================================================
# PDF PROCESSING
# ============================================================================

def process_pdf_file(pdf_path):
    """Extract text from a PDF file."""
    try:
        import pdfplumber
        
        text_content = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_content.append(f"--- Page {i+1} ---\n{page_text}")
        
        if text_content:
            return {"success": True, "content": "\n\n".join(text_content)}
        
        # Fallback to OCR if no text found
        print("  -> No text layer found, attempting OCR...")
        return {"success": False, "error": "PDF needs OCR processing"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# MAIN HARVESTER
# ============================================================================

def harvest_all_sources():
    """Main function to harvest all configured sources."""
    
    # Create directories
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    metadata = load_metadata()
    
    print("=" * 60)
    print("CBC Web Sources Harvester")
    print("=" * 60)
    print(f"Processing {len(SOURCE_URLS)} sources...")
    print()
    
    results = {
        "success": [],
        "failed": [],
        "needs_browser": []
    }
    
    for source_type, url in SOURCE_URLS:
        url_id = generate_id(url)
        
        # Check if already processed
        if url_id in metadata["sources"] and metadata["sources"][url_id].get("processed"):
            print(f"⏭️  Skipping (already processed): {url[:60]}...")
            continue
        
        print(f"📥 [{source_type.upper()}] {url[:70]}...")
        
        result = None
        
        if source_type == "article":
            result = extract_article_content(url)
        elif source_type == "google_share":
            result = extract_google_share_content(url)
        elif source_type == "facebook":
            result = extract_facebook_content(url)
        
        if result and result.get("success"):
            # Handle PDF downloads
            if result.get("type") == "pdf_download":
                pdf_result = process_pdf_file(result["file_path"])
                if pdf_result["success"]:
                    content = pdf_result["content"]
                else:
                    results["failed"].append({"url": url, "error": pdf_result["error"]})
                    continue
            else:
                content = result["content"]
            
            # Generate filename
            title = result.get("title", "")
            if not title:
                # Extract from URL or content
                title = url.split("/")[-1].split("?")[0] or f"source_{url_id}"
            
            filename = sanitize_filename(title)
            output_path = PROCESSED_DIR / f"{filename}.txt"
            
            # Add metadata header
            full_content = f"""Source URL: {url}
Harvested: {datetime.now().isoformat()}
Method: {result.get('method', 'unknown')}
---

{content}
"""
            
            # Save
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            print(f"   ✅ Saved: {output_path.name} ({len(content)} chars)")
            
            # Update metadata
            metadata["sources"][url_id] = {
                "url": url,
                "type": source_type,
                "processed": True,
                "output_file": str(output_path),
                "harvested_at": datetime.now().isoformat()
            }
            
            results["success"].append(url)
            
        elif result and result.get("needs_browser"):
            print(f"   ⚠️  Requires browser automation")
            results["needs_browser"].append(url)
            metadata["sources"][url_id] = {
                "url": url,
                "type": source_type,
                "processed": False,
                "needs_browser": True
            }
        else:
            error = result.get("error", "Unknown error") if result else "No result"
            print(f"   ❌ Failed: {error}")
            results["failed"].append({"url": url, "error": error})
    
    # Save metadata
    save_metadata(metadata)
    
    # Summary
    print()
    print("=" * 60)
    print("HARVEST SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully harvested: {len(results['success'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"⚠️  Need browser automation: {len(results['needs_browser'])}")
    
    if results["needs_browser"]:
        print()
        print("The following URLs need browser automation (Playwright):")
        for url in results["needs_browser"]:
            print(f"  - {url}")
    
    return results

# ============================================================================
# SYNC TO CHROMA CLOUD
# ============================================================================

def sync_to_cloud():
    """Sync all processed files to Chroma Cloud."""
    
    host = os.getenv('CHROMA_HOST', 'https://api.trychroma.com')
    api_key = os.getenv('CHROMA_API_KEY')
    tenant = os.getenv('CHROMA_TENANT')
    database = os.getenv('CHROMA_DATABASE')
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    
    if not all([api_key, tenant, database, hf_token]):
        print("❌ Missing environment variables. Please check .env file.")
        return False
    
    headers = {
        "x-chroma-token": api_key,
        "Content-Type": "application/json"
    }
    
    base_url = f"{host}/api/v2/tenants/{tenant}/databases/{database}"
    
    print()
    print("=" * 60)
    print("SYNCING TO CHROMA CLOUD")
    print("=" * 60)
    
    # Get or create collection
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
    
    # Sync all processed files
    files = list(PROCESSED_DIR.glob("*.txt"))
    print(f"Found {len(files)} files to sync...")
    
    synced = 0
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content:
            continue
        
        # Chunk for API safety
        chunk = content[:4000]
        
        # Generate embedding
        e_resp = requests.post(
            "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5",
            headers={"Authorization": f"Bearer {hf_token}"},
            json={"inputs": [chunk], "options": {"wait_for_model": True}}
        )
        
        if e_resp.status_code == 200:
            embedding = e_resp.json()[0]
            
            # Upsert to collection
            u_resp = requests.post(
                f"{base_url}/collections/{coll_id}/upsert",
                headers=headers,
                json={
                    "ids": [f"web_{file_path.stem}"],
                    "embeddings": [embedding],
                    "documents": [chunk],
                    "metadatas": [{"source": file_path.name, "type": "web_harvest"}]
                }
            )
            
            if u_resp.status_code in [200, 201]:
                print(f"  ✅ {file_path.name}")
                synced += 1
            else:
                print(f"  ❌ {file_path.name}: Upsert failed ({u_resp.status_code})")
        else:
            print(f"  ❌ {file_path.name}: Embedding failed ({e_resp.status_code})")
        
        # Rate limiting
        time.sleep(0.5)
    
    print()
    print(f"✅ Synced {synced}/{len(files)} files to Chroma Cloud")
    return True

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CBC Web Sources Harvester")
    parser.add_argument("--harvest", action="store_true", help="Harvest content from web sources")
    parser.add_argument("--sync", action="store_true", help="Sync processed files to Chroma Cloud")
    parser.add_argument("--all", action="store_true", help="Harvest and sync (full pipeline)")
    
    args = parser.parse_args()
    
    if args.all or (not args.harvest and not args.sync):
        # Default: run full pipeline
        print("Running full pipeline: Harvest -> Sync")
        harvest_all_sources()
        sync_to_cloud()
    elif args.harvest:
        harvest_all_sources()
    elif args.sync:
        sync_to_cloud()
