import requests
from urllib.parse import urlparse
import sys

def check_sitemap(domain):
    """
    Check if a domain has a sitemap by checking:
    1. robots.txt
    2. Common sitemap locations
    """
    
    # Ensure domain has protocol
    if not domain.startswith('http'):
        domain = f'https://{domain}'
    
    parsed = urlparse(domain)
    base_domain = parsed.netloc or parsed.path
    
    print(f"\n{'='*60}")
    print(f"Checking sitemaps for: {base_domain}")
    print(f"{'='*60}\n")
    
    found_sitemaps = []
    
    # 1. Check robots.txt
    print("🔍 Checking robots.txt...")
    try:
        robots_url = f'https://{base_domain}/robots.txt'
        response = requests.get(robots_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        
        if response.status_code == 200:
            print(f"✅ robots.txt found: {robots_url}")
            for line in response.text.split('\n'):
                if line.lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    found_sitemaps.append(sitemap_url)
                    print(f"   📄 Sitemap listed: {sitemap_url}")
        else:
            print(f"❌ robots.txt not found (status {response.status_code})")
    except Exception as e:
        print(f"❌ Error checking robots.txt: {e}")
    
    # 2. Check common sitemap locations
    print("\n🔍 Checking common sitemap locations...")
    
    common_paths = [
        f'https://{base_domain}/sitemap.xml',
        f'https://www.{base_domain}/sitemap.xml',
        f'https://{base_domain}/sitemap_index.xml',
        f'https://www.{base_domain}/sitemap_index.xml',
        f'https://{base_domain}/news-sitemap.xml',
        f'https://www.{base_domain}/news-sitemap.xml',
        f'https://{base_domain}/sitemap/sitemap.xml',
        f'https://{base_domain}/sitemaps/sitemap.xml',
        f'https://{base_domain}/sitemap_news.xml',
    ]
    
    for url in common_paths:
        if url in found_sitemaps:
            continue  # Already found in robots.txt
        
        try:
            response = requests.head(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True)
            if response.status_code == 200:
                found_sitemaps.append(url)
                print(f"✅ Found: {url}")
            elif response.status_code == 404:
                print(f"❌ Not found: {url}")
            else:
                print(f"⚠️  Status {response.status_code}: {url}")
        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout: {url}")
        except Exception as e:
            print(f"❌ Error: {url} - {str(e)[:50]}")
    
    # Summary
    print(f"\n{'='*60}")
    if found_sitemaps:
        print(f"✅ FOUND {len(found_sitemaps)} SITEMAP(S):")
        for sitemap in found_sitemaps:
            print(f"   • {sitemap}")
        print("\n💡 You can use these sitemap URLs in your config!")
    else:
        print("❌ NO SITEMAPS FOUND")
        print("\n💡 Alternative: Use DuckDuckGo search with site: operator")
        print(f"   Example: 'keyword site:{base_domain}'")
    print(f"{'='*60}\n")
    
    return found_sitemaps


def check_multiple_domains(domains):
    """Check sitemaps for multiple domains"""
    results = {}
    
    for domain in domains:
        sitemaps = check_sitemap(domain)
        results[domain] = sitemaps
    
    # Final summary
    print("\n" + "="*60)
    print("SUMMARY FOR ALL DOMAINS")
    print("="*60 + "\n")
    
    for domain, sitemaps in results.items():
        status = "✅" if sitemaps else "❌"
        print(f"{status} {domain}: {len(sitemaps)} sitemap(s) found")
    
    return results


if __name__ == "__main__":
    # Check if domains provided via command line
    if len(sys.argv) > 1:
        domains = sys.argv[1:]
        check_multiple_domains(domains)
    else:
        # Default: check common news sites
        print("No domains provided. Checking sample news sites...\n")
        print("Usage: python check_sitemaps.py domain1.com domain2.com ...")
        print("\nChecking sample sites:\n")
        
        sample_domains = [
            'bbc.com',
            'cnn.com',
            'reuters.com',
            'techcrunch.com',
            'theverge.com',
            'nytimes.com',
        ]
        
        check_multiple_domains(sample_domains)
