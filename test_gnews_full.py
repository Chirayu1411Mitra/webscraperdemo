from gnews import GNews

google_news = GNews()
news = google_news.get_news("AI")
if news:
    url = news[0]['url']
    print(f"Original URL: {url}")
    article = google_news.get_full_article(url)
    if article:
        print(f"Resolved Article Title: {article.title}")
        print(f"Resolved Article Text Length: {len(article.text)}")
    else:
        print("Failed to resolve article.")
