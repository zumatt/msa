import os
import pandas as pd
import urllib.parse
from datetime import datetime
from duckduckgo_search import DDGS
from scholarly import scholarly
import requests
from dotenv import load_dotenv
from time import sleep
from pyzenodo3 import Zenodo
import signal
import sys
from pathlib import Path
import time

# Load environment variables
load_dotenv(override=True)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Set up signal handler for Ctrl+C
def signal_handler(sig, frame):
    print('\n\n👋 Happy research...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def get_location():
    try:
        response = requests.get('https://ipapi.co/json/')
        if response.status_code == 200:
            data = response.json()
            return f"{data.get('city', '')}, {data.get('country_name', '')}"
    except Exception as e:
        print(f"⚠️ Error getting location: {e}")
        return "No location found"

def search_google(query, max_results):
    print("🔍 Searching Google...")
    results = []
    
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        print("❌ Google API credentials are missing. Please check your .env file.")
        return results
    
    try:
        for start in range(1, max_results + 1, 10):
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": GOOGLE_API_KEY,
                "cx": GOOGLE_CSE_ID,
                "q": query,
                "start": start
            }
            
            print(f"📡 Making request to Google API (start={start})...")
            response = requests.get(url, params=params)
            
            # Print response status and headers for debugging
            print(f"📊 Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Error response: {response.text}")
                if response.status_code == 403:
                    print("💡 Tip: Your API key might be invalid or the Custom Search API might not be enabled.")
                elif response.status_code == 429:
                    print("💡 Tip: You might have exceeded your daily quota.")
                break
            
            data = response.json()
            
            # Process results
            items = data.get("items", [])
            if not items:
                print("ℹ️ No more results found.")
                break
                
            for item in items:
                results.append((
                    "Google",
                    datetime.utcnow().isoformat(),
                    get_location(),
                    query,
                    item["link"],
                    item["title"],
                    item.get("snippet", "")
                ))
            
            # Add a small delay between requests
            sleep(1)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print(f"✅ Found {len(results)} results from Google")
    return results

def search_duckduckgo(query, max_results):
    print("🦆 Searching DuckDuckGo...")
    results = []
    
    try:
        print(f"🔍 Query: {query}")
        print("📡 Initializing DuckDuckGo search...")
        
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(query, max_results=max_results), 1):
                try:
                    print(f"📚 Fetching result {i}/{max_results}...")
                    
                    # Print debug information
                    print(f"📄 Title: {r.get('title', 'No title')}")
                    print(f"🔗 URL: {r.get('href', 'No URL')}")
                    print("---")
                    
                    results.append((
                        "DuckDuckGo",
                        datetime.utcnow().isoformat(),
                        get_location(),
                        query,
                        r.get("href", ""),
                        r.get("title", ""),
                        r.get("body", "")
                    ))
                    
                except Exception as e:
                    print(f"⚠️ Error processing DuckDuckGo result: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ DuckDuckGo search failed: {e}")
        print("💡 Tip: Check your internet connection or try again later.")
    
    print(f"✅ Found {len(results)} results from DuckDuckGo")
    return results

def search_google_scholar(query, max_results):
    print("🎓 Searching Google Scholar...")
    results = []
    
    try:
        print(f"🔍 Query: {query}")
        print("📡 Initializing Google Scholar search...")
        search_query = scholarly.search_pubs(query)
        
        for i in range(max_results):
            try:
                print(f"📚 Fetching result {i+1}/{max_results}...")
                pub = next(search_query)
                
                # Extract authors from the bib dictionary
                authors = pub.get("bib", {}).get("author", [])
                author_str = ", ".join(authors) if authors else "Unknown Author"
                
                # Get the abstract, ensuring it's not too long
                abstract = pub.get("bib", {}).get("abstract", "")
                if len(abstract) > 1000:  # Truncate long abstracts
                    abstract = abstract[:997] + "..."
                
                # Get the publication year
                year = pub.get("bib", {}).get("pub_year", "")
                
                # Get the venue
                venue = pub.get("bib", {}).get("venue", "")
                
                # Create a more detailed title including year and venue
                detailed_title = f"{pub.get('bib', {}).get('title', 'Untitled')}"
                if year:
                    detailed_title += f" ({year})"
                if venue:
                    detailed_title += f" - {venue}"
                
                # Print debug information
                print(f"📄 Title: {detailed_title}")
                print(f"👥 Authors: {author_str}")
                print(f"📊 Citations: {pub.get('num_citations', 0)}")
                print(f"🔗 URL: {pub.get('pub_url', 'No URL available')}")
                print("---")
                
                results.append((
                    "Google Scholar",
                    datetime.utcnow().isoformat(),
                    get_location(),
                    query,
                    pub.get("pub_url", ""),
                    detailed_title,
                    f"Authors: {author_str}\n\nAbstract: {abstract}\n\nCitations: {pub.get('num_citations', 0)}"
                ))
                
            except StopIteration:
                print("ℹ️ No more results available")
                break
            except Exception as e:
                print(f"⚠️ Error processing Scholar result: {e}")
                print(f"💡 Tip: This might be due to rate limiting or temporary access issues")
                continue
        
    except Exception as e:
        print(f"❌ Google Scholar search failed: {e}")
        print("💡 Tip: Google Scholar may be blocking requests. Try again later or use a different search engine.")
    
    print(f"✅ Found {len(results)} results from Google Scholar")
    return results

def search_zenodo(query, max_results):
    print("🔬 Searching Zenodo...")
    results = []
    
    try:
        print(f"🔍 Query: {query}")
        print("📡 Initializing Zenodo search...")
        
        base_url = "https://zenodo.org/api/records"
        params = {
            'q': query,
            'size': min(max_results, 100),  # Zenodo API limit is 100 per request
            'sort': 'mostrecent',
            'type': 'publication'
        }
        
        print("📡 Making request to Zenodo API...")
        response = requests.get(base_url, params=params)
        
        # Print response status and headers for debugging
        print(f"📊 Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Error response: {response.text}")
            if response.status_code == 429:
                print("💡 Tip: Rate limit reached. Try again later.")
            return results
        
        data = response.json()
        hits = data.get('hits', {}).get('hits', [])
        
        for i, item in enumerate(hits, 1):
            try:
                print(f"📚 Processing result {i}/{len(hits)}...")
                
                # Get metadata
                metadata = item.get('metadata', {})
                
                # Get creators
                creators = metadata.get('creators', [])
                creator_names = [creator.get('name', 'Unknown Author') for creator in creators]
                creator_str = ', '.join(creator_names) if creator_names else 'Unknown Author'
                
                # Get description and clean HTML tags
                description = metadata.get('description', '')
                if description:
                    description = description.replace('<p>', '').replace('</p>', '\n')
                    description = description.replace('<br>', '\n')
                    description = ' '.join(description.split())
                
                # Get DOI if available
                doi = metadata.get('doi', '')
                link = f"https://doi.org/{doi}" if doi else item.get('links', {}).get('html', '')
                
                # Print debug information
                print(f"📄 Title: {metadata.get('title', 'Untitled')}")
                print(f"👥 Authors: {creator_str}")
                print(f"🔗 URL: {link}")
                print("---")
                
                results.append((
                    "Zenodo",
                    metadata.get('publication_date', datetime.utcnow().isoformat()),
                    get_location(),
                    query,
                    link,
                    f"{metadata.get('title', 'Untitled')} - {creator_str}",
                    description
                ))
                
            except Exception as e:
                print(f"⚠️ Error processing Zenodo result: {e}")
                continue
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print(f"✅ Found {len(results)} results from Zenodo")
    return results

def perform_search(query, max_results, selected_tools):
    print(f"\n🔎 Performing search for: '{query}'")
    all_results = []

    if "google" in selected_tools:
        all_results += search_google(query, max_results)
    
    if "duckduckgo" in selected_tools:
        all_results += search_duckduckgo(query, max_results)
    
    if "google_scholar" in selected_tools:
        all_results += search_google_scholar(query, max_results)
        
    if "zenodo" in selected_tools:
        all_results += search_zenodo(query, max_results)

    if not all_results:
        print("⚠️ No results found from any selected search engines")
        return

    df = pd.DataFrame(all_results, columns=[
        "Search Engine", "Date of Search", "Location", "Search Query",
        "Result Link", "Result Title", "Result Description"
    ])

    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Create timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = urllib.parse.quote_plus(query)
    filename = output_dir / f"{timestamp}_{safe_query}.ods"
    
    # Save to ODS
    df.to_excel(filename, engine="odf", index=False)
    print(f"✅ Saved {len(df)} results to {filename}")

if __name__ == "__main__":
    # Example usage
    selected_tools = ["google", "duckduckgo", "google_scholar", "zenodo"]
    perform_search("test query", max_results=10, selected_tools=selected_tools)