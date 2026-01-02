# Web Scraper 

A Flask-based web application that scrapes news articles from multiple sources and provides AI-powered summarization.

## Getting Started

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd webscraperdemo
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Configure websites:
- Edit `config/websites.json` to add or modify news sources

### Running the Application

Start the Flask development server:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Tech Stack

### Backend
- **Python 3.8+** - Core programming language
- **Flask** - Web framework for the application
- **Transformers** - Hugging Face library for AI summarization
- **PyTorch** - Deep learning framework for AI models

### Web Scraping
- **newspaper3k** - Article extraction and parsing
- **requests** - HTTP library for fetching web content
- **lxml** - XML/HTML processing with html_clean support
- **ddgs** - DuckDuckGo search API for article discovery

### Frontend
- **HTML/CSS/JavaScript** - Web interface
- **Bootstrap** (if applicable) - UI framework

### Data Storage
- **JSON** - Configuration and scraped data storage

## Project Structure
```
webscraperdemo/
├── app.py              # Flask application entry point
├── scraper.py          # Web scraping logic
├── ai_processor.py     # AI summarization functionality
├── check_sitemaps.py   # Sitemap validation utility
├── requirements.txt    # Python dependencies
├── config/
│   └── websites.json   # Website configuration
├── data/              # Scraped data output (gitignored)
├── static/            # CSS and JavaScript files
└── templates/         # HTML templates
```

## Features
- Multi-source news scraping
- Sitemap-based article discovery
- DuckDuckGo fallback search
- AI-powered article summarization
- Web-based user interface


