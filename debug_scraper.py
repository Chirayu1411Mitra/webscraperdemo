from scraper import fetch_news

print("Fetching news...")
articles = fetch_news("AI", max_results=3)
for i, article in enumerate(articles):
    text = article.get('text', '')
    print(f"Article {i+1}: {article['title']}")
    print(f"URL: {article['url']}")
    print(f"Text Length: {len(text)}")
    print(f"Word Count: {len(text.split())}")
    print(f"Text Preview: {text[:100]}...")
    print("-" * 20)
