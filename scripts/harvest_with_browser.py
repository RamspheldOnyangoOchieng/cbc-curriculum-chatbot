"""
Browser-Based Content Harvester
================================
Uses Playwright for JavaScript-rendered pages like:
- Facebook posts
- Google Share links that redirect
- Protected/dynamic content

Run with: python scripts/harvest_with_browser.py
"""

import os
import sys
import re
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# Force UTF-8 for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

BROWSER_URLS = [
    # Google Share Links (may need JS rendering)
    ("google_share", "KEMIS System Tracking Students", "https://share.google/ysiS84EjNPpW9qtVr"),
    ("google_share", "36 Best Career Paths Pure Sciences", "https://share.google/PcEId2FS9sTjhEd1s"),
    ("google_share", "Sports And Recreation Careers", "https://share.google/Y3oFHuGLKN7ILbzDj"),
    ("google_share", "History Citizenship 13 Careers", "https://share.google/RPxQqmVWwcAPWyqoF"),
    ("google_share", "CBC Senior School Subject Combinations", "https://share.google/lhWOkHDjYvXnGCDjd"),
    ("google_share", "Subject Combinations Senior Schools PDF", "https://share.google/Zqi2vKPgrN8LBpTNX"),
    ("google_share", "36 Career Paths Alt Link", "https://share.google/rUIoMFwWPM5GDhvLt"),
    ("google_share", "PS Bitok Grade Nine Placement", "https://share.google/Mw1saVG0j0sgD27fO"),
    ("google_share", "KNEC Portals", "https://share.google/tApOoaRWB5ecNXADM"),
    ("google_share", "2026 Registration Circular Nairobi", "https://share.google/Hpk3J1RZPmm595Iym"),
    ("google_share", "Digital Content Kenya Education Cloud", "https://share.google/I84rzVCWqx1FncR9O"),
    ("google_share", "CBC AI App Assessment", "https://share.google/qM3bMUxegFZoVWFQ9"),
    ("google_share", "KICD Kenya Curriculum Development", "https://share.google/zMKYKGMhqWTFaHbF9"),
    
    # Facebook
    ("facebook", "CBC Education Update Post", "https://m.facebook.com/story.php?story_fbid=pfbid0k9NCbgaQ81DTykYDUr1PqT4UVvjwnJ2LjemEVwLYx8VzXTW2y4LKUG9zHuFrT6X4l&id=100004655256269"),
]

PROCESSED_DIR = Path("data/processed")
DOWNLOAD_DIR = Path("data/raw_downloads")

# ============================================================================
# BROWSER HARVESTER
# ============================================================================

async def harvest_with_browser():
    """Use Playwright to harvest content from dynamic pages."""
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright not installed. Installing now...")
        os.system(f"{sys.executable} -m pip install playwright")
        os.system(f"{sys.executable} -m playwright install chromium")
        from playwright.async_api import async_playwright
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("BROWSER-BASED CONTENT HARVESTER")
    print("=" * 60)
    print(f"Processing {len(BROWSER_URLS)} URLs...")
    print()
    
    results = {"success": [], "failed": []}
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ignore_https_errors=True
        )
        
        # Set up download handling
        context.set_default_timeout(60000)  # 60 second timeout
        
        page = await context.new_page()
        
        for source_type, title, url in BROWSER_URLS:
            print(f"🌐 [{source_type.upper()}] {title}")
            print(f"   URL: {url[:70]}...")
            
            try:
                # Navigate to URL
                response = await page.goto(url, wait_until='networkidle')
                
                # Wait for content to load
                await page.wait_for_timeout(3000)
                
                # Get final URL after redirects
                final_url = page.url
                print(f"   -> Final URL: {final_url[:70]}")
                
                content = ""
                
                # Handle Google Docs/Drive
                if 'docs.google.com' in final_url:
                    # For Google Docs, try to get the content
                    content = await page.evaluate('''() => {
                        const doc = document.querySelector('.kix-page-content-wrapper');
                        if (doc) return doc.innerText;
                        
                        // Fallback: get all text
                        return document.body.innerText;
                    }''')
                    
                elif 'drive.google.com' in final_url:
                    # For Drive preview, try to extract visible content
                    content = await page.evaluate('''() => {
                        // Try PDF preview text
                        const viewer = document.querySelector('.drive-viewer-paginated-page');
                        if (viewer) return viewer.innerText;
                        
                        // Try to get any visible text
                        return document.body.innerText;
                    }''')
                    
                    # If it's a PDF, we might need to download it
                    if len(content.strip()) < 100:
                        print("   -> Attempting PDF download...")
                        # Look for download button
                        try:
                            download_btn = page.locator('[aria-label*="Download"]').first
                            if await download_btn.is_visible():
                                async with page.expect_download() as download_info:
                                    await download_btn.click()
                                download = await download_info.value
                                save_path = DOWNLOAD_DIR / f"{title.replace(' ', '_')}.pdf"
                                await download.save_as(str(save_path))
                                print(f"   -> Downloaded: {save_path.name}")
                                content = f"[PDF Downloaded: {save_path}]"
                        except Exception as e:
                            print(f"   -> Download failed: {e}")
                
                elif 'facebook.com' in final_url:
                    # Facebook: extract post content
                    content = await page.evaluate('''() => {
                        // Try to get main post
                        const post = document.querySelector('[data-ad-preview="message"]') ||
                                     document.querySelector('[data-testid="post_message"]') ||
                                     document.querySelector('.userContent') ||
                                     document.querySelector('div[dir="auto"]');
                        
                        if (post) return post.innerText;
                        
                        // Fallback: get body text, remove nav elements
                        const body = document.body.cloneNode(true);
                        body.querySelectorAll('nav, header, footer, script, style').forEach(el => el.remove());
                        return body.innerText;
                    }''')
                    
                else:
                    # Generic page: extract main content
                    content = await page.evaluate('''() => {
                        // Try article or main content first
                        const article = document.querySelector('article') ||
                                        document.querySelector('main') ||
                                        document.querySelector('[role="main"]') ||
                                        document.querySelector('.content');
                        
                        if (article) return article.innerText;
                        
                        // Fallback: clean body text
                        const body = document.body.cloneNode(true);
                        body.querySelectorAll('nav, header, footer, script, style, aside').forEach(el => el.remove());
                        return body.innerText;
                    }''')
                
                # Clean content
                if content:
                    # Remove excessive whitespace
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    content = '\n'.join(lines)
                
                # Save if we got meaningful content
                if content and len(content) > 100:
                    filename = sanitize_filename(title)
                    output_path = PROCESSED_DIR / f"{filename}.txt"
                    
                    full_content = f"""Title: {title}
Source URL: {url}
Final URL: {final_url}
Harvested: {datetime.now().isoformat()}
Method: playwright_browser
---

{content}
"""
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(full_content)
                    
                    print(f"   ✅ Saved: {output_path.name} ({len(content)} chars)")
                    results["success"].append(url)
                else:
                    print(f"   ⚠️ Minimal content extracted ({len(content) if content else 0} chars)")
                    results["failed"].append({"url": url, "reason": "minimal_content"})
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
                results["failed"].append({"url": url, "error": str(e)})
            
            # Be nice to servers
            await page.wait_for_timeout(2000)
        
        await browser.close()
    
    # Summary
    print()
    print("=" * 60)
    print("BROWSER HARVEST SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully harvested: {len(results['success'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    
    return results

def sanitize_filename(text, max_length=80):
    """Create a safe filename from text."""
    safe = re.sub(r'[^\w\s-]', '', text)
    safe = re.sub(r'[-\s]+', '_', safe).strip('_')
    return safe[:max_length]

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    asyncio.run(harvest_with_browser())
