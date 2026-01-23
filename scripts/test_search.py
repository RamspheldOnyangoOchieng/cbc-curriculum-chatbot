
import os
import sys
from dotenv import load_dotenv

# Force UTF-8 for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from cbc_bot.retriever import CBCRetriever

load_dotenv()

def test_drill():
    query = "Is the system achieving its purpose?"
    print(f"Testing Word-by-Word Deep Drill for: '{query}'")
    
    retriever = CBCRetriever()
    context = retriever.find_relevant_context(query, n_results=5)
    
    print("\n--- RETRIEVED CONTEXT ---")
    if context:
        # Show first 500 chars of each fragment (assuming join by \n\n---\n\n)
        fragments = context.split("\n\n---\n\n")
        print(f"Total Fragments Found: {len(fragments)}")
        for i, frag in enumerate(fragments):
            print(f"\nFragment {i+1}:")
            print(frag[:400] + "...")
    else:
        print("No context retrieved. Deep Drill might need debugging.")

if __name__ == "__main__":
    test_drill()
