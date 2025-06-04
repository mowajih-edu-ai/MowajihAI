
import asyncio
import re
import os
import base64 # Not directly used in the final version, but kept for context if screenshot functionality is re-added
import litellm # Used by ChatLiteLLM internally
import html # Not directly used in the final version
from urllib.parse import urljoin, urlparse

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

from langchain_community.chat_models.litellm import ChatLiteLLM
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

# --- CONFIGURATIONS (can be adjusted or passed as arguments) ---
# These are for crawl4ai's internal run for each URL.
# The 'recursive_depth' parameter in recursive_crawl_and_filter controls the overall recursion.
CRAWL4AI_MAX_DEPTH_PER_STEP = 0 # How deep crawl4ai goes for each URL in a recursive step (1 for immediate links)
CRAWL4AI_MAX_PAGES_PER_STEP = 20 # Max pages crawl4ai fetches for each URL in a recursive step
SCREENSHOT = False  # Set to True to take screenshots of the pages (requires handling base64 output)
IFRAMES = False  # Set to True to process iframe content

# --- LLM Configuration ---
# Ensure DEEPSEEK_API_KEY is set in your environment variables.
# Example: os.environ["DEEPSEEK_API_KEY"] = "your_deepseek_api_key_here"
LLM_MODEL_NAME = "deepseek/deepseek-chat"



# Define your starting URL and the filtering prompt
initial_url = "https://www.fsdm.usmba.ac.ma/"
# initial_url = "https://www.uca.ma/fr"
# initial_url = "https://fst-usmba.ac.ma/"
# initial_url = "https://www.tawjihnet.net/"
filter_prompt = "informations sur les formations et programmes de formation et les diplômes"

# Set the recursive depth:
# 0: Only crawl and filter the initial_url.
# 1: Crawl initial_url, filter. Then, for each filtered link, crawl it and filter its links.
# 2: ... and so on.
recursive_depth = 1 
    

def url_to_filename(url):
    # Remove protocol (http:// or https://)
    url = re.sub(r'^https?://', '', url)
    # Replace non-alphanumeric characters with underscores
    filename = re.sub(r'[^A-Za-z0-9._-]', '_', url)
    return filename


script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, 'scraped', url_to_filename(initial_url))
os.makedirs(output_dir, exist_ok=True) # Creates the folder if it doesn't exist
debug_log_file = os.path.join(output_dir, 'debug_log.txt')
with open(debug_log_file, 'w', encoding='utf-8') as f:
    f.write("--- Debug Log for Recursive Crawl and Filter ---\n")


def filter_links_with_ai(links: list[dict], prompt: str) -> list[dict]:
    """
    Given a list of link dictionaries (with 'text', 'title', and 'href'),
    uses an LLM to filter them based on the provided prompt.
    Returns a list of relevant link dictionaries.
    """
    # Remove duplicate links by href to avoid redundant processing
    seen_hrefs = set()
    unique_links = []
    for link in links:
        href = link.get('href')
        if href and href not in seen_hrefs:
            unique_links.append(link)
            seen_hrefs.add(href)
    links = unique_links

    if not links:
        print("No links to filter.")
        return []

    # Initialize the LLM with LiteLLM integration
    # Temperature is set low to encourage focused, factual responses (URLs only)
    llm = ChatLiteLLM(model=LLM_MODEL_NAME, litellm_api_key=os.getenv("DEEPSEEK_API_KEY"), temperature=0.1)
    
    # Define the prompt template for the LLM
    filter_prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are an expert at identifying relevant URLs from a list based on a given topic. "
                   "Your response must ONLY contain the URLs, one per line. "
                   "Do not include any introductory text, explanations, numbering, or additional formatting."),
        ("user", "Given the following list of links (with their text, title, and URLs), "
                 "which ones are most likely to contain information about '{prompt}'?\n"
                 "Return only the URLs, one per line, that are plausible sources for this topic.\n\n"
                 "Links:\n{links_str}")
    ])

    # Create a Langchain chain: Prompt -> LLM -> Output Parser
    chain = filter_prompt_template | llm | StrOutputParser()

    # Split links into batches to avoid hitting the LLM's context window limits
    batch_size = 500
    filtered_links_accumulator = []

    print(f"Filtering {len(links)} links with AI...")
    for i in range(0, len(links), batch_size):
        batch = links[i:i + batch_size]
        # Format the batch of links into a string for the LLM
        batch_links_str = "\n".join([
            f"TEXT: {link.get('text','N/A')} | TITLE: {link.get('title','N/A')} | URL: {link['href']}"
            for link in batch
        ])
        
        try:
            # Invoke the LLM chain with the current batch of links
            response_text = chain.invoke({"prompt": prompt, "links_str": batch_links_str})
            # print(f"--- AI Response for batch {i//batch_size + 1} ---\n{response_text}\n--- End AI Response ---") # For debugging
        except Exception as e:
            print(f"Error calling LLM for batch {i//batch_size + 1}: {e}")
            continue

        # Extract plausible URLs from the AI's response using a regex pattern
        # This is robust against extra text the LLM might generate.
        url_pattern = r'https?://[^\s)>\]]+'
        plausible_urls = []
        for line in response_text.splitlines():
            match = re.search(url_pattern, line)
            if match:
                plausible_urls.append(match.group(0))
        
        # Add links from the current batch that match the plausible URLs returned by the AI
        filtered_links_accumulator.extend([link for link in batch if link['href'] in plausible_urls])

    return filtered_links_accumulator


async def crawl_single_url_and_get_links(url: str, crawl_depth: int = CRAWL4AI_MAX_DEPTH_PER_STEP, max_pages_per_crawl: int = CRAWL4AI_MAX_PAGES_PER_STEP) -> list[dict]:
    """
    Crawls a single URL using crawl4ai and extracts its internal links.
    Args:
        url: The URL to crawl.
        crawl_depth: The maximum depth for this specific crawl4ai run (e.g., 1 for immediate links).
        max_pages_per_crawl: Max pages for this specific crawl4ai run.
    Returns:
        A flattened list of unique internal link dictionaries ({'text': ..., 'href': ...}).
    """
    # Configure crawl4ai for a shallow crawl from the given URL
    crawler_config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=crawl_depth,
            # max_pages=max_pages_per_crawl,
            include_external=False # Only collect internal links
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=False, # Keep verbose off for cleaner programmatic output
        screenshot=SCREENSHOT,
        process_iframes=IFRAMES,
        cache_mode=CacheMode.ENABLED, # Enable caching to speed up repeated crawls
    )

    all_internal_links = []
    try:
        async with AsyncWebCrawler() as crawler:
            results = await crawler.arun(url, config=crawler_config)
            for result in results:
                # Iterate through all pages crawled in this run and collect their internal links
                for link in result.links.get('internal', []):
                    # Ensure the link is a dictionary and has a valid 'href'
                    if isinstance(link, dict) and 'href' in link and link['href']:
                        all_internal_links.append(link)
    except Exception as e:
        print(f"Error during crawl4ai run for {url}: {e}")
        return []
    
    # Remove duplicate links based on their href
    seen_hrefs = set()
    unique_links = []
    for link in all_internal_links:
        if link['href'] not in seen_hrefs:
            unique_links.append(link)
            seen_hrefs.add(link['href'])
    
    return unique_links


async def recursive_crawl_and_filter(
    start_url: str, 
    llm_prompt: str, 
    max_recursive_depth: int, 
    current_depth: int = 0,
    crawled_results: dict = None, # Accumulator for all filtered results across recursion
    visited_urls: set = None # To prevent re-processing the same URL in different recursive paths
) -> dict:
    """
    Recursively crawls a starting URL, filters its links using an LLM,
    and then repeats the process for the filtered links up to a specified depth.

    Args:
        start_url: The URL to begin the crawling and filtering process.
        llm_prompt: The prompt used by the LLM to filter relevant links.
        max_recursive_depth: Controls how many times the crawl-and-filter cycle repeats.
                             - 0: Only crawls and filters the initial `start_url`.
                             - 1: Crawls `start_url`, filters. Then, for each filtered link,
                                  crawls it and filters its links.
                             - N: Repeats the process N times.
        current_depth: Internal parameter tracking the current recursion depth.
        crawled_results: Internal dictionary to accumulate results (URL -> list of filtered links).
        visited_urls: Internal set to keep track of URLs already processed to prevent infinite loops.

    Returns:
        A dictionary where keys are the URLs that were crawled, and values are
        lists of filtered link dictionaries found on those URLs.
    """
    if crawled_results is None:
        crawled_results = {}
    if visited_urls is None:
        visited_urls = set()



    # Normalize URL to ensure uniqueness for visited_urls check
    # This helps prevent re-crawling the same page due to minor URL variations (e.g., query params, fragments)
    parsed_url = urlparse(start_url)
    normalized_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path.rstrip('/')

    if normalized_url in visited_urls:
        # print(f"Skipping already visited URL: {normalized_url}") # For debugging
        return crawled_results
    
    visited_urls.add(normalized_url)

    if current_depth > max_recursive_depth:
        print(f"Reached max recursive depth ({max_recursive_depth}). Stopping for {start_url}.")
        return crawled_results

    print(f"\n--- Processing: {start_url} (Recursive Depth: {current_depth}/{max_recursive_depth}) ---")

    # Step 1: Crawl the current URL and get all internal links
    all_links_from_current_url = await crawl_single_url_and_get_links(start_url, CRAWL4AI_MAX_DEPTH_PER_STEP, CRAWL4AI_MAX_PAGES_PER_STEP)
    print(f"Found {len(all_links_from_current_url)} internal links on {start_url}")
    if all_links_from_current_url:
        # write to a file in the output_dir for debugging
        with open(debug_log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n--- Links from {start_url} ---\n")
            for link in all_links_from_current_url:
                f.write(f"{link.get('text', 'N/A')} | {link.get('title', 'N/A')} | {link['href']}\n")

    # Step 2: Filter the links using AI
    filtered_links_for_current_url = filter_links_with_ai(all_links_from_current_url, llm_prompt)
    crawled_results[start_url] = filtered_links_for_current_url
    print(f"Filtered down to {len(filtered_links_for_current_url)} relevant links for {start_url}")

    # Step 4: Recursively repeat for filtered links if max_recursive_depth not reached
    if current_depth < max_recursive_depth:
        for link_dict in filtered_links_for_current_url:
            next_url = link_dict.get('href')
            if next_url:
                # Resolve relative URLs to absolute URLs for subsequent crawling
                if not next_url.startswith(('http://', 'https://')):
                    next_url = urljoin(start_url, next_url)
                
                await recursive_crawl_and_filter(
                    next_url, 
                    llm_prompt, 
                    max_recursive_depth, 
                    current_depth + 1, 
                    crawled_results,
                    visited_urls
                )
    
    return crawled_results

# --- Example Usage ---
async def main():
    
    print(f"Starting recursive crawl and filter from: {initial_url}")
    print(f"Filtering for: '{filter_prompt}'")
    print(f"Recursive depth: {recursive_depth}")

    final_results = await recursive_crawl_and_filter(initial_url, filter_prompt, recursive_depth)

    # Remove duplicate links based on their href
    seen_hrefs = set()
    unique_links = []
    unique_hrefs = []
    for links in final_results.values():
            if links:
                for link in links:
                    if link['href'] not in seen_hrefs:
                        unique_links.append(link)
                        unique_hrefs.append(link['href'])
                        seen_hrefs.add(link['href'])

    print(f"REMOVED DUPLICATES {len(unique_links)}")
    
    # Append unique links to the file
    with open(debug_log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n--- Unique Filtered Links {len(unique_links)} ---\n")
        for link in unique_links:
            f.write(f"{link.get('text', 'N/A')} | {link.get('title', 'N/A')} | {link.get('href', 'N/A')}\n")
    
    print("\n--- Final Consolidated Filtered Links ---")
    if not unique_links:
        print("No relevant links found or an error occurred.")
    else:
        for link in unique_links:
                print(f"  - Text: {link.get('text', 'N/A')} | Title: {link.get('title', 'N/A')} | URL: {link.get('href', 'N/A')}")
    
    
    # scrap screenshots of unique_links
    
    crawler_config = CrawlerRunConfig(
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=False, # Keep verbose off for cleaner programmatic output
        screenshot=True,
        process_iframes=True,
        cache_mode=CacheMode.ENABLED, # Enable caching to speed up repeated crawls
    )

    all_internal_links = []
    try:
        async with AsyncWebCrawler() as crawler:
            results = await crawler.arun_many(unique_hrefs, config=crawler_config)
            for result in results:
                # Iterate through all pages crawled in this run and collect their internal links
                if result.screenshot:
                    print(f"Screenshot available: {result.screenshot is not None}")
                    screenshot_dir = os.path.join(output_dir, 'screenshots')
                    os.makedirs(screenshot_dir, exist_ok=True)  # Creates the folder if it doesn't exist
                    with open(f"{screenshot_dir}/ss_{url_to_filename(result.url)}.png", "wb") as f:
                        f.write(base64.b64decode(result.screenshot))
                
    except Exception as e:
        print(f"Error during crawl4ai run for {url}: {e}")
        return []

if __name__ == "__main__":
    # Run the asynchronous main function
    asyncio.run(main())