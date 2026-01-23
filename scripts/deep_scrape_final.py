
import asyncio
from playwright.async_api import async_playwright
import sys
import codecs
from pathlib import Path

# Force UTF-8
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

async def deep_scrape_final():
    url = "https://thekenyatimes.com/opinions/grade-10-school-placement-crisis/"
    print(f"Deep Scraping specific P tags: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a real mobile device user agent to try and get a simplified view
        device = p.devices['iPhone 13']
        context = await browser.new_context(**device, ignore_https_errors=True)
        page = await context.new_page()
        
        try:
            # Add headers to look more like a browser
            await page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/"
            })
            
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(7000) # Give it time to load
            
            # Try to get the title
            title = await page.title()
            
            # Extract all paragraphs that have a decent length
            paragraphs = await page.evaluate('''() => {
                const ps = Array.from(document.querySelectorAll('p, .entry-content div, .post-content p'));
                return ps.map(p => p.innerText.trim()).filter(t => t.length > 40);
            }''')
            
            if paragraphs:
                full_text = "\n\n".join(paragraphs)
                output_file = Path("data/processed/Grade_10_Placement_Crisis_Deep_Final.txt")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(f"Title: {title}\nSource: {url}\n\n{full_text}")
                print(f"✅ Extracted {len(paragraphs)} paragraphs. Total {len(full_text)} chars.")
            else:
                # Last ditch effort - get everything from body
                body_text = await page.inner_text('body')
                print(f"⚠️ Only found body text ({len(body_text)} chars). Saving body.")
                with open("data/processed/Grade_10_Placement_Crisis_Body.txt", "w", encoding="utf-8") as f:
                    f.write(body_text)

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(deep_scrape_final())
