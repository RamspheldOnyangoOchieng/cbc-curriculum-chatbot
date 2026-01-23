
import trafilatura
import sys
import codecs
from pathlib import Path

# Force UTF-8 for Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def deep_scrape():
    url = "https://thekenyatimes.com/opinions/grade-10-school-placement-crisis/"
    print(f"Fetching: {url}")
    
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        print("Failed to download content.")
        return
        
    result = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
    
    if result:
        print(f"Extracted {len(result)} characters.")
        output_file = Path("data/processed/Grade_10_Placement_Crisis_Deep.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Saved to {output_file}")
    else:
        print("Trafilatura failed to extract text.")

if __name__ == "__main__":
    deep_scrape()
