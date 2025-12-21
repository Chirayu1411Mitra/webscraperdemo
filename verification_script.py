
import time
from ai_processor import NewsFilter

def test_model_speed():
    print("Initializing model...")
    start_init = time.time()
    nf = NewsFilter()
    print(f"Model initialized in {time.time() - start_init:.2f}s")

    dummy_articles = [{
        'title': 'Test Article',
        'url': 'http://example.com',
        'published_date': '2023-01-01',
        'text': 'Artificial Intelligence is transforming the world. ' * 50 # ~250 words
    }]

    print("Processing article...")
    start_proc = time.time()
    results = nf.process_articles(dummy_articles)
    duration = time.time() - start_proc
    
    print(f"Processing took {duration:.2f}s")
    print(f"Result summary: {results[0]['summary']}")
    
    if duration < 5.0:
        print("SUCCESS: Processing is fast enough.")
    else:
        print("WARNING: Processing might still be too slow.")

if __name__ == "__main__":
    test_model_speed()
