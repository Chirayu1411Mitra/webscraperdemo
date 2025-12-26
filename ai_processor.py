from transformers import pipeline
import torch

class NewsFilter:
    def __init__(self, model_name="sshleifer/distilbart-cnn-12-6"):
        """
        Initializes the summarization pipeline.
        """
        print(f"Loading AI model: {model_name}...")
        device = 0 if torch.cuda.is_available() else -1
        self.summarizer = pipeline("summarization", model=model_name, device=device)
        print("Model loaded.")

    def process_articles(self, articles):
        """
        Filters and summarizes a list of articles.
        """
        processed_data = []
        
        for article in articles:
            text = article.get('text', '')
            if not text or len(text.split()) < 10:
                # Skip only completely empty or extremely short (broken) articles
                print(f"Skipping article with insufficient text: {len(text.split())} words.")
                continue
                
            try:
                # Truncate text to avoid token limit issues (simple truncation)
                # BART has a limit of 1024 tokens. We'll take the first ~3000 chars as a rough proxy.
                input_text = text[:3000] 
                
                summary_list = self.summarizer(input_text, max_length=130, min_length=30, do_sample=False)
                summary = summary_list[0]['summary_text']
                
                processed_data.append({
                    'title': article['title'],
                    'url': article['url'],
                    'published_date': str(article['published_date']) if article['published_date'] else None,
                    'summary': summary
                })
            except Exception as e:
                print(f"Error summarizing article {article['title'][:30]}...: {e}")
                
        return processed_data

if __name__ == "__main__":
    # Test the processor
    dummy_articles = [{
        'title': 'Test Article',
        'url': 'http://example.com',
        'published_date': '2023-01-01',
        'text': 'Artificial Intelligence is transforming the world. ' * 20
    }]
    nf = NewsFilter()
    print(nf.process_articles(dummy_articles))
