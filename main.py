from bs4 import BeautifulSoup
import requests
import webbrowser
import time
import sys
from urllib.parse import urlparse

# --- Configuration ---

FEEDS = {
    "Top Stories": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "India": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "World": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
    "Business": "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
    "Sports": "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms",
    "Tech": "https://timesofindia.indiatimes.com/rssfeeds/66949542.cms",
    "Entertainment": "https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms",
}

CACHE_DURATION = 300  # 5 minutes in seconds
CACHE = {}  # {genre: {'data': parsed_soup_entries, 'timestamp': time.time()}}

ALLOWED_DOMAINS = [
    "timesofindia.indiatimes.com",
    "www.timesofindia.indiatimes.com",
    "economictimes.indiatimes.com",
    "m.timesofindia.com"
]

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

# --- Functions ---

def fetch_feed(genre):
    """
    Fetches the RSS feed for the given genre and returns a list of entry dictionaries.
    Uses in-memory caching to avoid repeated requests within CACHE_DURATION.
    """
    url = FEEDS.get(genre)
    if not url:
        print(f"Error: No URL found for genre '{genre}'")
        return None

    # Check cache
    if genre in CACHE:
        cached_entry = CACHE[genre]
        if time.time() - cached_entry['timestamp'] < CACHE_DURATION:
            # print("DEBUG: Serving from cache") 
            return cached_entry['data']

    print(f"Fetching {genre} headlines...")
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        response.raise_for_status()
        
        # Parse the content using BeautifulSoup with XML parser
        soup = BeautifulSoup(response.content, features='xml')
        
        items = soup.find_all('item')
        if not items:
            print(f"Warning: No entries found in feed for {genre}.")
            return None

        # Parse items immediately to cache the data structure
        entries = []
        for item in items:
            title_tag = item.find('title')
            link_tag = item.find('link')
            pubdate_tag = item.find('pubDate')
            
            title = title_tag.text.strip() if title_tag else 'No Title'
            link = link_tag.text.strip() if link_tag else ''
            published = pubdate_tag.text.strip() if pubdate_tag else ''
            
            entries.append({
                'title': title,
                'link': link,
                'published': published
            })

        # Update cache
        CACHE[genre] = {
            'data': entries,
            'timestamp': time.time()
        }
        return entries

    except requests.exceptions.RequestException as e:
        print(f"Network error fetching feed: {e}")
        return None
    except Exception as e:
        print(f"Error parsing feed: {e}")
        return None

def get_top_entries(entries, n=10):
    """
    Extracts the top N entries from the parsed list.
    Returns a list of dictionaries with index, title, link, published date.
    """
    if not entries:
        return []
    
    result = []
    for i, entry in enumerate(entries[:n]):
        result.append({
            'index': i + 1,
            'title': entry['title'],
            'link': entry['link'],
            'published': entry['published']
        })
    return result

def is_allowed_url(url):
    """
    Validates if the URL belongs to an allowed domain.
    """
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        if not hostname:
            return False
        
        for allowed in ALLOWED_DOMAINS:
            if hostname == allowed or hostname.endswith("." + allowed):
                return True
        
        # Special check for indiatimes.com general subdomains if strict check fails
        if "indiatimes.com" in hostname:
            return True
            
        return False
    except Exception:
        return False

def open_article(url):
    """
    Opens the article in the default web browser after validation.
    """
    if not url:
        print("Error: Invalid URL.")
        return

    if is_allowed_url(url):
        print(f"Opening article: {url}")
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Failed to open browser: {e}")
    else:
        print(f"Security Warning: URL host not allowed ({url}). Opening blocked.")

def display_menu(options):
    """
    Displays a numbered menu and returns the user's choice.
    """
    print("\n--- Times of India CLI ---")
    print("Select a Genre:")
    for i, option in enumerate(options):
        print(f"{i + 1}. {option}")
    print("0. Exit")
    
    choice = input("\nEnter choice: ").strip()
    return choice

def display_headlines(genre, entries):
    """
    Displays the list of headlines for a genre.
    """
    print(f"\n--- {genre} Top 10 Headlines ---")
    for entry in entries:
        pub_date = f" ({entry['published']})" if entry['published'] else ""
        print(f"{entry['index']}. {entry['title']}{pub_date}")

# --- Main Loop ---

def main():
    genres = list(FEEDS.keys())
    
    while True:
        choice = display_menu(genres)
        
        if choice == '0':
            print("Exiting...")
            break
        
        if not choice.isdigit():
            print("Invalid input. Please enter a number.")
            continue
            
        index = int(choice) - 1
        if 0 <= index < len(genres):
            genre = genres[index]
            entries_list = fetch_feed(genre)
            
            if entries_list:
                entries = get_top_entries(entries_list)
                if not entries:
                    print("No headlines available.")
                    continue
                
                # Headline interaction loop
                while True:
                    display_headlines(genre, entries)
                    print("\nEnter article number to open (or 0 to go back):")
                    article_choice = input("> ").strip()
                    
                    if article_choice == '0':
                        break
                    
                    if not article_choice.isdigit():
                        print("Invalid input.")
                        continue
                        
                    article_index = int(article_choice) - 1
                    if 0 <= article_index < len(entries):
                        article = entries[article_index]
                        open_article(article['link'])
                    else:
                        print("Invalid article number.")
        else:
            print("Invalid genre selection.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
