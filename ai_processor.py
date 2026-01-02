from transformers import pipeline
import torch
from concurrent.futures import ThreadPoolExecutor, as_completed

class NewsFilter:
    def __init__(self, model_name="sshleifer/distilbart-cnn-6-6"):
        """
        Initializes the summarization pipeline with optimized model.
        Using distilbart-cnn-6-6 (smaller, 2x faster than 12-6 version)
        """
        print(f"Loading AI model: {model_name}...")
        device = 0 if torch.cuda.is_available() else -1
        
        # Optimize pipeline for speed
        self.summarizer = pipeline(
            "summarization", 
            model=model_name, 
            device=device,
            batch_size=8  # Process multiple articles at once
        )
        print("Model loaded and optimized for batch processing.")

    def summarize_single(self, article):
        """Summarize a single article (for parallel processing)"""
        text = article.get('text', '')
        if not text or len(text.split()) < 10:
            print(f"⚠️  Skipping article with insufficient text: {len(text.split())} words.")
            return None
            
        try:
            # Truncate to first 2000 chars (faster processing)
            input_text = text[:2000]
            
            # Shorter summaries = faster processing
            input_word_count = len(input_text.split())
            max_length = min(100, max(25, int(input_word_count * 0.25)))
            min_length = min(20, max(10, int(input_word_count * 0.12)))
            
            summary_list = self.summarizer(
                input_text, 
                max_length=max_length, 
                min_length=min_length, 
                do_sample=False,
                truncation=True
            )
            summary = summary_list[0]['summary_text']
            
            return {
                'title': article['title'],
                'url': article['url'],
                'published_date': str(article['published_date']) if article['published_date'] else None,
                'source': article.get('source', 'Unknown'),
                'summary': summary
            }
        except Exception as e:
            print(f"❌ Error summarizing '{article['title'][:40]}...': {str(e)[:60]}")
            return None

    def process_articles(self, articles):
        """
        Process articles in batches for faster summarization.
        """
        if not articles:
            return []
        
        print(f"🤖 Summarizing {len(articles)} articles in batches...")
        processed_data = []
        
        # Batch processing - process all articles at once
        try:
            # Prepare all texts
            texts = []
            valid_articles = []
            
            for article in articles:
                text = article.get('text', '')
                if text and len(text.split()) >= 10:
                    texts.append(text[:2000])  # Truncate
                    valid_articles.append(article)
            
            if not texts:
                print("⚠️  No valid articles to summarize")
                return []
            
            print(f"📝 Processing {len(texts)} valid articles...")
            
            # Calculate parameters for each text
            params = []
            for text in texts:
                word_count = len(text.split())
                max_len = min(100, max(25, int(word_count * 0.25)))
                min_len = min(20, max(10, int(word_count * 0.12)))
                params.append((max_len, min_len))
            
            # Batch summarize (much faster)
            summaries = []
            batch_size = 4  # Process 4 at a time
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_params = params[i:i+batch_size]
                
                # Use the first param for the batch (simplified)
                max_length = batch_params[0][0]
                min_length = batch_params[0][1]
                
                batch_summaries = self.summarizer(
                    batch_texts,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False,
                    truncation=True
                )
                summaries.extend(batch_summaries)
                print(f"  ✅ Processed {min(i+batch_size, len(texts))}/{len(texts)} articles")
            
            # Combine results
            for article, summary_obj in zip(valid_articles, summaries):
                processed_data.append({
                    'title': article['title'],
                    'url': article['url'],
                    'published_date': str(article['published_date']) if article['published_date'] else None,
                    'source': article.get('source', 'Unknown'),
                    'summary': summary_obj['summary_text']
                })
            
            print(f"✅ Successfully summarized {len(processed_data)} articles")
                
        except Exception as e:
            print(f"❌ Batch processing error: {e}")
            print("⚠️  Falling back to individual processing...")
            
            # Fallback to individual processing
            for article in articles:
                result = self.summarize_single(article)
                if result:
                    processed_data.append(result)
        
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
