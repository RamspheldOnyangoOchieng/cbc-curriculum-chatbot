
import asyncio
from playwright.async_api import async_playwright
import re
from pathlib import Path
from datetime import datetime

import sys
import codecs

# Force UTF-8 for Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

async def scrape_specific_article():
    url = "https://thekenyatimes.com/opinions/grade-10-school-placement-crisis/"
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Deep Scraping: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000) # Wait for JS rendering
            
            # Target the article content specifically
            content = await page.evaluate('''() => {
                const article = document.querySelector('article') || document.body;
                // Remove nav, sidebar, ads, footer
                const clone = article.cloneNode(true);
                clone.querySelectorAll('nav, header, footer, aside, .sidebar, .ads, script, style').forEach(el => el.remove());
                return clone.innerText;
            }''')
            
            title = await page.title()
            
            if len(content) > 500:
                # Clean up
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                clean_text = '\n'.join(lines)
                
                filename = "Grade_10_Placement_Crisis_Opinion.txt"
                with open(output_dir / filename, "w", encoding="utf-8") as f:
                    f.write(f"Title: {title}\nSource: {url}\nDate: {datetime.now()}\n\n{clean_text}")
                
                print(f"✅ Success! Saved {len(clean_text)} characters to {filename}")
                return True
            else:
                print(f"❌ Failed: Only retrieved {len(content)} characters.")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_specific_article())
