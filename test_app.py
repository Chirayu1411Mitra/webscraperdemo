import requests
import json

def test_scrape(keyword):
    url = 'http://127.0.0.1:5000/scrape'
    headers = {'Content-Type': 'application/json'}
    data = {'keyword': keyword, 'count': 1}
    
    print(f"Testing with keyword: {keyword}")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            print("Success!")
            results = response.json().get('results', [])
            for item in results:
                print(f"Title: {item['title']}")
                print(f"Summary: {item['summary'][:100]}...")
        else:
            print(f"Failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 30)

if __name__ == "__main__":
    # Test Keyword
    test_scrape("AI")
    # Test Direct URL (using the one we found earlier)
    test_scrape("https://www.cnbc.com/2025/11/26/mit-study-finds-ai-can-already-replace-11point7percent-of-us-workforce.html")
