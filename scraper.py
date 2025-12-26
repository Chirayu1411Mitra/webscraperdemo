from gnews import GNews
from newspaper import Article
from googlenewsdecoder import new_decoderv1
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_news(keyword, max_results=5):
    """
    Fetches news articles based on a keyword using Google News (via gnews).
    Returns a list of dictionaries containing title, link, published date, and full text.
    """
    logger.info(f"Fetching news for keyword: {keyword}")
    
    articles_data = []

    # Check if the keyword is actually a URL
    if keyword.startswith("http://") or keyword.startswith("https://"):
        logger.info(f"Detected URL: {keyword}. Scraping directly...")
        try:
            article = Article(keyword)
            article.download()
            article.parse()
            return [{
                'title': article.title,
                'url': keyword,
                'published_date': article.publish_date,
                'text': article.text
            }]
        except Exception as e:
            logger.error(f"Failed to scrape URL {keyword}: {e}")
            return []

    # Google News Search using GNews
    try:
        google_news = GNews(max_results=max_results)
        results = google_news.get_news(keyword)
        
        if not results:
             logger.warning(f"No results found for {keyword} on Google News.")
             return []
             
        logger.info(f"Found {len(results)} articles. Fetching content...")

        for item in results:
            url = item.get('url')
            title = item.get('title')
            date = item.get('published date') 

            if not url:
                continue

            try:
                # Add a small delay to be polite
                time.sleep(0.5)
                
                # Decode Google News URL to get the real article URL
                target_url = url
                try:
                    decoded = new_decoderv1(url)
                    if decoded.get("status"):
                        target_url = decoded["decoded_url"]
                        logger.info(f"Decoded to: {target_url}")
                except Exception as e:
                    logger.warning(f"URL decoding failed for {url}: {e}")

                # Use newspaper3k directly on the resolved URL
                article = Article(target_url)
                article.download()
                article.parse()
                
                if not article:
                    logger.warning(f"Failed to create article object for {target_url}")
                    continue

                # Check for empty content (e.g. paywall or failed scrape)
                if not article.text or len(article.text.strip()) == 0:
                    logger.warning(f"Skipping empty content from {url}")
                    continue

                articles_data.append({
                    'title': article.title if article.title else title, # Prefer article title
                    'url': article.url if article.url else url,         # Prefer resolved URL
                    'published_date': article.publish_date if article.publish_date else date,
                    'text': article.text
                })
                logger.info(f"Fetched: {title[:30]}...")
                
            except Exception as e:
                logger.error(f"Failed to fetch {url}: {e}")
                
    except Exception as e:
        logger.error(f"Google News Search failed: {e}")

    return articles_data

if __name__ == "__main__":
    # Test the scraper
    data = fetch_news("India", max_results=2)
    print(data)
