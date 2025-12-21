import argparse
from scraper import fetch_news
from ai_processor import NewsFilter
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="AI-Powered News Scraper & Filter")
    parser.add_argument("keyword", help="Keyword to search for (e.g., 'India')")
    parser.add_argument("--count", type=int, default=5, help="Number of articles to fetch")
    parser.add_argument("--output", help="Output CSV file name", default="news_summary.csv")
    
    args = parser.parse_args()
    
    print(f"--- Starting News Scraper for keyword: '{args.keyword}' ---")
    
    # 1. Fetch News
    articles = fetch_news(args.keyword, max_results=args.count)
    
    if not articles:
        print("No articles found.")
        return

    # 2. Process with AI
    print("\n--- Initializing AI Model for Summarization ---")
    ai_filter = NewsFilter()
    
    print(f"\n--- Processing {len(articles)} articles ---")
    summarized_news = ai_filter.process_articles(articles)
    
    # 3. Display and Save Results
    print("\n--- Results ---")
    for item in summarized_news:
        print(f"\nTitle: {item['title']}")
        print(f"Summary: {item['summary']}")
        print(f"Link: {item['url']}")
        print("-" * 40)
        
    if summarized_news:
        df = pd.DataFrame(summarized_news)
        df.to_csv(args.output, index=False)
        print(f"\nSaved results to {args.output}")
    else:
        print("No articles could be summarized.")

if __name__ == "__main__":
    main()
