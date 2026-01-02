from newspaper import Article
from ddgs import DDGS
import logging
import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from datetime import datetime, timedelta
import time

# Configure logging with better formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Helper function for formatted output
def log_header(message):
    """Print a formatted header in logs"""
    logger.info("="*70)
    logger.info(f"  {message}")
    logger.info("="*70)

def log_section(message):
    """Print a section separator"""
    logger.info("-"*70)
    logger.info(f"  {message}")
    logger.info("-"*70)


def search_sitemap(keyword, domain, sitemap_url, max_results=5):
    """
    Search for articles in sitemap XML that match the keyword.
    Returns list of article URLs, or None if sitemap fails (triggers DuckDuckGo fallback).
    """
    logger.info(f"Searching sitemap for '{keyword}' on {domain}")
    
    try:
        response = requests.get(sitemap_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            logger.warning(f"⚠️  Sitemap failed (HTTP {response.status_code}): {sitemap_url}")
            return None  # Return None to trigger DuckDuckGo fallback
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        # Handle sitemap namespaces
        namespaces = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'news': 'http://www.google.com/schemas/sitemap-news/0.9'
        }
        
        article_urls = []
        keyword_lower = keyword.lower()
        
        # Check if this is a sitemap index (contains links to other sitemaps)
        sitemap_entries = root.findall('.//ns:sitemap', namespaces)
        if sitemap_entries:
            logger.info(f"Found sitemap index with {len(sitemap_entries)} sub-sitemaps")
            # Recursively fetch from first few sub-sitemaps
            for sitemap_entry in sitemap_entries[:3]:  # Limit to first 3 sub-sitemaps
                loc = sitemap_entry.find('ns:loc', namespaces)
                if loc is not None:
                    sub_urls = search_sitemap(keyword, domain, loc.text, max_results)
                    article_urls.extend(sub_urls)
                    if len(article_urls) >= max_results:
                        break
            return article_urls[:max_results]
        
        # Parse regular sitemap entries
        url_entries = root.findall('.//ns:url', namespaces)
        
        for url_entry in url_entries:
            loc = url_entry.find('ns:loc', namespaces)
            if loc is None:
                continue
            
            url = loc.text
            
            # Check lastmod date (prefer recent articles - last 30 days)
            lastmod = url_entry.find('ns:lastmod', namespaces)
            if lastmod is not None:
                try:
                    article_date = datetime.fromisoformat(lastmod.text.replace('Z', '+00:00'))
                    if datetime.now(article_date.tzinfo) - article_date > timedelta(days=30):
                        continue  # Skip old articles
                except:
                    pass
            
            # Check if keyword appears in URL or title
            if keyword_lower in url.lower():
                article_urls.append(url)
                logger.info(f"  Found match in URL: {url}")
                if len(article_urls) >= max_results:
                    break
        
        logger.info(f"📄 Found {len(article_urls)} matching articles from sitemap")
        return article_urls[:max_results] if article_urls else None
        
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"❌ Sitemap parsing error ({error_type}): {str(e)[:100]}")
        return None  # Return None to trigger DuckDuckGo fallback


def search_duckduckgo(keyword, domain, max_results=5):
    """
    Search DuckDuckGo for articles matching keyword on specific domain.
    Returns list of article URLs.
    """
    logger.info(f"🔍 Searching DuckDuckGo: '{keyword}' on {domain}")
    
    try:
        query = f"{keyword} site:{domain}"
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        article_urls = []
        for result in results:
            url = result.get('href')
            if url:
                # Filter out common non-article pages
                skip_patterns = [
                    '/category/', '/topic/', '/tag/', '/author/', '/writer/', '/page/',
                    '/election/', '/constituency/', '/candidates/',
                    '/biography/', '/bio/', '/profile/', '/about/',
                    '.pdf', '.jpg', '.png', '.gif',
                    '/static_pages/', '/privacy', '/terms',
                    '/contact', '/advertise'
                ]
                if any(pattern in url.lower() for pattern in skip_patterns):
                    logger.debug(f"  Skipping non-article URL: {url}")
                    continue
                
                # Skip if URL is just the homepage
                parsed = urlparse(url)
                if parsed.path in ['', '/']:
                    logger.debug(f"  Skipping homepage: {url}")
                    continue
                    
                article_urls.append(url)
                logger.debug(f"  ✓ {result.get('title', 'No title')[:60]}...")
        
        logger.info(f"🔍 Found {len(article_urls)} articles from DuckDuckGo")
        return article_urls
        
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"❌ DuckDuckGo search error ({error_type}): {str(e)[:100]}")
        return []


def scrape_article(url, max_retries=2):
    """
    Scrape a single article using newspaper3k with retry logic.
    Returns article data dict or None if failed.
    """
    for attempt in range(max_retries):
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            # Check for empty content (lowered threshold to 50 chars)
            text_length = len(article.text.strip()) if article.text else 0
            if text_length < 50:
                logger.warning(f"Skipping article with insufficient content ({text_length} chars): {url}")
                return None
            
            # Check if title exists
            if not article.title or len(article.title.strip()) < 3:
                logger.warning(f"Skipping article with no valid title: {url}")
                return None
            
            # Extract domain/source from URL
            parsed_url = urlparse(article.url)
            source_domain = parsed_url.netloc.replace('www.', '')
            
            return {
                'title': article.title,
                'url': article.url,
                'published_date': article.publish_date,
                'text': article.text,
                'source': source_domain
            }
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 2s, 4s
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Only log on final failure
                logger.error(f"Failed to scrape article {url}: {str(e)[:80]}")
                return None


def check_article_relevance(article_data, keyword):
    """
    Check if article is relevant to the keyword.
    Returns True if relevant, False otherwise.
    """
    if not article_data:
        return False
    
    keyword_lower = keyword.lower()
    title = article_data.get('title', '').lower()
    text = article_data.get('text', '').lower()
    url = article_data.get('url', '').lower()
    
    # Skip biography/profile indicators
    bio_indicators = ['biography', 'profile', 'about', 'who is', 'early life', 'personal life']
    if any(indicator in title.lower() for indicator in bio_indicators):
        logger.info(f"Skipping biography/profile page: {article_data.get('title', 'No title')[:50]}")
        return False
    
    # Check if keyword appears in title (strong relevance signal)
    if keyword_lower in title:
        return True
    
    # Count keyword occurrences in text
    keyword_count = text.count(keyword_lower)
    
    # Calculate keyword density (occurrences per 100 words)
    word_count = len(text.split())
    if word_count < 50:
        return False
    
    keyword_density = (keyword_count / word_count) * 100
    
    # Require at least 2 mentions or 0.5% density for longer articles
    if keyword_count >= 2 or keyword_density >= 0.5:
        logger.debug(f"Relevant: '{keyword}' appears {keyword_count} times ({keyword_density:.2f}% density)")
        return True
    
    logger.info(f"Low relevance: '{keyword}' only appears {keyword_count} time(s) in {article_data.get('title', 'article')[:50]}")
    return False


def fetch_news(keyword, websites_config, max_results=5):
    """
    Fetches news articles based on keyword from configured websites.
    Uses sitemap if available, otherwise falls back to DuckDuckGo search.
    
    Args:
        keyword: Search keyword
        websites_config: List of website dicts with 'domain', 'sitemap', 'enabled'
        max_results: Max articles per website
    
    Returns:
        List of article dictionaries with title, url, published_date, text
    """
    log_header(f"STARTING SEARCH: '{keyword}'")
    
    # Check if the keyword is actually a URL
    if keyword.startswith("http://") or keyword.startswith("https://"):
        logger.info("🔗 Direct URL detected, scraping single article...")
        article_data = scrape_article(keyword)
        return [article_data] if article_data else []
    
    # Filter enabled websites
    enabled_sites = [w for w in websites_config if w.get('enabled', True)]
    logger.info(f"🌐 Searching across {len(enabled_sites)} enabled websites")
    logger.info(f"📊 Max results per site: {max_results}")
    
    all_article_urls = []
    url_to_source = {}  # Map URLs to their source website names
    site_stats = {}  # Track URLs found per site
    
    # Search each website (parallel)
    log_section("PHASE 1: Searching for article URLs")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_site = {}
        
        for site in enabled_sites:
            domain = site.get('domain')
            sitemap = site.get('sitemap', '').strip()
            site_name = site.get('name', domain)
            
            logger.info(f"📡 {site_name}: {'Sitemap' if sitemap else 'DuckDuckGo'}")
            
            if sitemap:
                # Use sitemap search
                future = executor.submit(search_sitemap, keyword, domain, sitemap, max_results)
            else:
                # Use DuckDuckGo fallback
                future = executor.submit(search_duckduckgo, keyword, domain, max_results)
            
            future_to_site[future] = (site_name, domain, sitemap)
        
        # Collect results as they complete
        for future in as_completed(future_to_site):
            site_name, domain, sitemap = future_to_site[future]
            try:
                urls = future.result()
                
                # If sitemap failed (returned None), try DuckDuckGo as fallback
                if urls is None and sitemap:
                    logger.warning(f"⚠️  {site_name}: Sitemap failed, trying DuckDuckGo fallback...")
                    urls = search_duckduckgo(keyword, domain, max_results)
                
                if urls:
                    all_article_urls.extend(urls)
                    # Map each URL to its source
                    for url in urls:
                        url_to_source[url] = site_name
                    site_stats[site_name] = len(urls)
                    logger.info(f"✅ {site_name}: Found {len(urls)} article(s)")
                else:
                    site_stats[site_name] = 0
                    logger.info(f"ℹ️  {site_name}: No articles found")
            except Exception as e:
                site_stats[site_name] = 0
                error_type = type(e).__name__
                logger.error(f"❌ {site_name} failed ({error_type}): {str(e)[:80]}")
    
    log_section("SEARCH RESULTS SUMMARY")
    logger.info(f"📊 Total URLs found: {len(all_article_urls)}")
    for site_name, count in sorted(site_stats.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"   • {site_name}: {count} URL(s)")
    
    if not all_article_urls:
        logger.warning("❌ No articles found across all websites")
        return []
    
    # Scrape articles (parallel)
    log_section("PHASE 2: Scraping article content")
    
    articles_data = []
    scraped_count = 0
    filtered_count = 0
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(scrape_article, url): url for url in all_article_urls}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                article_data = future.result()
                if article_data:
                    # Check relevance before adding
                    if check_article_relevance(article_data, keyword):
                        # Add source information
                        article_data['source'] = url_to_source.get(url, 'Unknown')
                        articles_data.append(article_data)
                        scraped_count += 1
                        logger.info(f"✅ [{scraped_count}] {article_data['title'][:60]}...")
                    else:
                        filtered_count += 1
                        logger.debug(f"⚠️  Filtered (low relevance): {article_data.get('title', 'No title')[:50]}")
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                error_type = type(e).__name__
                logger.error(f"❌ Scraping error ({error_type}): {str(e)[:80]}")
    
    # Final summary
    log_header("SCRAPING COMPLETE")
    logger.info(f"✅ Successfully scraped: {scraped_count} article(s)")
    logger.info(f"⚠️  Filtered (irrelevant): {filtered_count} article(s)")
    logger.info(f"❌ Failed to scrape: {failed_count} article(s)")
    logger.info(f"📊 Success rate: {(scraped_count / len(all_article_urls) * 100):.1f}%" if all_article_urls else "")
    
    # Per-website breakdown
    if articles_data:
        log_section("ARTICLES PER WEBSITE")
        source_counts = {}
        for article in articles_data:
            source = article.get('source', 'Unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   📰 {source}: {count} article(s)")
    
    logger.info("="*70)
    return articles_data


if __name__ == "__main__":
    # Test the scraper
    import json
    
    # Load config
    with open('config/websites.json', 'r') as f:
        config = json.load(f)
    
    websites = config['websites']
    data = fetch_news("Army", websites, max_results=3)
    
    print(f"\n{'='*60}")
    print(f"Found {len(data)} articles")
    print(f"{'='*60}")
    for article in data:
        print(f"\n{article['title']}")
        print(f"URL: {article['url']}")
        print(f"Text length: {len(article['text'])} chars")
