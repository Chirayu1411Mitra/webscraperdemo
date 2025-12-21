from googlenewsdecoder import new_decoderv1
from gnews import GNews

google_news = GNews()
news = google_news.get_news("AI")
if news:
    url = news[0]['url']
    print(f"Original URL: {url}")
    try:
        decoded_url = new_decoderv1(url)
        if decoded_url.get("status"):
            print(f"Decoded URL: {decoded_url['decoded_url']}")
        else:
            print("Failed to decode URL.")
    except Exception as e:
        print(f"Error decoding: {e}")
