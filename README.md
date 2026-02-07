# ⚡ Real-Time Web Scraper

A powerful, real-time web scraping application that searches DuckDuckGo and extracts relevant content from search results. Built with Flask-SocketIO for instant result streaming and a modern, glassmorphic UI.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- **Real-Time Results**: See scraped content appear instantly as it's collected via WebSocket connections
- **Concurrent Scraping**: Asynchronous HTTP/2 requests with configurable concurrency (up to 28 concurrent connections)
- **Smart Content Extraction**: Extracts only relevant sentences containing your search keyword
- **Modern UI**: Beautiful glassmorphic design with smooth animations and live progress tracking
- **Flexible Date Ranges**: Filter search results by time period (24 hours, week, month, year)
- **Dual Modes**: 
  - **CLI Mode** (`app.py`): Terminal-based scraper with console output
  - **Web Mode** (`server.py`): Real-time web interface with live updates
- **Data Export**: Automatically saves results to JSON files with metadata

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd webscraperdemo
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 📖 Usage

### Web Interface (Recommended)

1. **Start the server**
   ```bash
   python server.py
   ```

2. **Open your browser**
   - Navigate to `http://localhost:5000`

3. **Start scraping**
   - Enter your search keyword
   - Select a date range
   - Click "Search" and watch results appear in real-time!

### Command Line Interface

1. **Run the CLI scraper**
   ```bash
   python app.py
   ```

2. **Enter your keyword** when prompted

3. **View results** in the terminal and check the generated JSON file

## 🛠️ Configuration

### Date Range Options

Modify the `DATE_RANGE` variable in `app.py` or select from the dropdown in the web interface:

- `"d"` - Past 24 hours
- `"w"` - Past week
- `"m"` - Past month
- `"y"` - Past year
- `None` - All time (no date filter)

### Concurrency Settings

Adjust the `max_concurrent` parameter in the scraping functions:

```python
# In app.py or server.py
scrape_all(result_urls, keyword, max_concurrent=28)
```

> **Note**: Higher values increase speed but may trigger rate limiting on some websites.

### Search Region

Change the search region in the DuckDuckGo query:

```python
results = ddgs.text(
    query=keyword,
    region="in-en",  # Change to "wt-wt" for global or other region codes
    # ...
)
```

## 📦 Dependencies

- **Flask** - Web framework
- **Flask-SocketIO** - WebSocket support for real-time communication
- **Flask-CORS** - Cross-Origin Resource Sharing
- **httpx** - Async HTTP client with HTTP/2 support
- **BeautifulSoup4** - HTML parsing
- **lxml** - Fast XML/HTML parser
- **duckduckgo-search** - DuckDuckGo search API wrapper

## 📁 Project Structure

```
webscraperdemo/
├── app.py              # CLI-based scraper
├── server.py           # Flask-SocketIO web server
├── index.html          # Modern web interface
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🎯 How It Works

1. **Search**: Queries DuckDuckGo with your keyword and date range
2. **Collect URLs**: Extracts up to 50 search result URLs
3. **Concurrent Scraping**: Fetches all URLs simultaneously using async HTTP/2
4. **Content Extraction**: 
   - Removes noise (scripts, styles, navigation, etc.)
   - Extracts sentences containing the keyword
   - Returns up to 7 relevant sentences per page
5. **Real-Time Streaming**: Results are sent to the browser as they're scraped
6. **Data Export**: Saves all results to a timestamped JSON file

## 📊 Output Format

Results are saved as JSON files with the following structure:

```json
{
  "keyword": "your search term",
  "date_range": "d",
  "timestamp": "2026-02-07T17:54:12",
  "total_urls_found": 50,
  "successful_scrapes": 42,
  "elapsed_time_seconds": 8.45,
  "results": [
    {
      "url": "https://example.com/article",
      "content": "Relevant sentences containing your keyword..."
    }
  ]
}
```

## 🎨 UI Features

- **Glassmorphic Design**: Modern frosted-glass aesthetic with backdrop blur
- **Live Statistics**: Real-time counters for URLs found, successful scrapes, and elapsed time
- **Progress Bar**: Visual feedback during the scraping process
- **Animated Cards**: Smooth slide-in animations for each result
- **Connection Status**: Live WebSocket connection indicator
- **Responsive Layout**: Adapts to different screen sizes

## 🔧 Troubleshooting

### Connection Issues

If you see "Disconnected" in the web interface:
- Ensure `server.py` is running
- Check that port 5000 is not blocked by firewall
- Verify the WebSocket URL in `index.html` matches your server address

### Scraping Failures

Some websites may block automated requests:
- The scraper uses a realistic User-Agent header
- HTTP/2 support helps with modern websites
- Failed requests are silently skipped (no error shown)

### Performance

If scraping is slow:
- Increase `max_concurrent` (default: 28)
- Check your internet connection
- Some websites may have rate limiting

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## ⚠️ Disclaimer

This tool is for educational purposes. Always respect websites' `robots.txt` files and terms of service. Use responsibly and ethically.

---

**Made with ❤️ using Flask, SocketIO, and modern web technologies**
