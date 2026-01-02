from flask import Flask, render_template, request, jsonify
from scraper import fetch_news
from ai_processor import NewsFilter
import os
import json
from datetime import datetime

app = Flask(__name__)

# Load website configuration
print("Loading website configuration...")
try:
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'websites.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    WEBSITES = config.get('websites', [])
    enabled_count = sum(1 for w in WEBSITES if w.get('enabled', True))
    print(f"✓ Loaded {len(WEBSITES)} websites ({enabled_count} enabled)")
    
    # Show which sites use sitemap vs DuckDuckGo
    sitemap_count = sum(1 for w in WEBSITES if w.get('enabled', True) and w.get('sitemap', '').strip())
    ddg_count = enabled_count - sitemap_count
    print(f"  • {sitemap_count} sites with sitemaps")
    print(f"  • {ddg_count} sites using DuckDuckGo fallback")
except FileNotFoundError:
    print("⚠ Warning: config/websites.json not found. Using empty config.")
    WEBSITES = []
except Exception as e:
    print(f"⚠ Error loading config: {e}")
    WEBSITES = []

# Initialize AI Model (lazy loading or global)
# Loading it globally might take time on startup, but better for request speed.
print("Initializing AI Model...")
ai_filter = NewsFilter()
print("AI Model Ready.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    keyword = data.get('keyword')
    count = data.get('count', 3)
    
    if not keyword:
        return jsonify({'error': 'Keyword or URL is required'}), 400
    
    try:
        print(f"Received request for: {keyword}")
        articles = fetch_news(keyword, WEBSITES, max_results=int(count))
        
        if not articles:
            return jsonify({'message': 'No articles found.'}), 404
            
        print(f"Fetched {len(articles)} articles. Processing...")
        summarized_news = ai_filter.process_articles(articles)
        
        print(f"AI processing complete. Sending {len(summarized_news)} summaries to frontend.")
        
        # Save to JSON
        try:
            data_dir = os.path.join(os.getcwd(), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_data_{timestamp}.json"
            filepath = os.path.join(data_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summarized_news, f, indent=4, ensure_ascii=False)
                
            print(f"Data saved to {filepath}")
        except Exception as e:
            print(f"Failed to save data to JSON: {e}")

        return jsonify({'results': summarized_news})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
