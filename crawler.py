import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from rag import RAGHandler

# Configuration
START_URL = "https://yourwebsite.com"
MAX_PAGES = 50  # Limit to 50 pages for this initial run to be fast
DELAY = 1  # Seconds between requests

# Initialize State
visited_urls = set()
queue = [START_URL]
rag = RAGHandler()

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme) and "yourwebsite.com" in parsed.netloc

def clean_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.extract()
        
    text = soup.get_text(separator='\n')
    
    # Break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # Drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text, soup.title.string if soup.title else "No Title"

def crawl():
    count = 0
    while queue and count < MAX_PAGES:
        current_url = queue.pop(0)
        
        if current_url in visited_urls:
            continue
            
        print(f"Crawling ({count+1}/{MAX_PAGES}): {current_url}")
        visited_urls.add(current_url)
        
        try:
            response = requests.get(current_url, headers={"User-Agent": "RZBBot/1.0"}, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch {current_url}: {response.status_code}")
                continue
                
            # Content Type Check
            if "text/html" not in response.headers.get("Content-Type", ""):
                print(f"Skipping non-HTML: {current_url}")
                continue

            content, title = clean_text(response.content)
            
            # Ingest into RAG
            rag.ingest_text(content, {"source": current_url, "title": title})
            
            # Find new links
            soup = BeautifulSoup(response.content, 'html.parser')
            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    full_url = urljoin(current_url, href)
                    # Normalize: remove fragments
                    full_url = full_url.split('#')[0]
                    if is_valid_url(full_url) and full_url not in visited_urls and full_url not in queue:
                        queue.append(full_url)
            
            count += 1
            time.sleep(DELAY)
            
        except Exception as e:
            print(f"Error crawling {current_url}: {e}")

if __name__ == "__main__":
    print(f"Starting crawl of {START_URL}...")
    crawl()
    print("Crawl complete. Data ingested into ChromaDB.")
