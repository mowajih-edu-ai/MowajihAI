
import asyncio
import re
import os
import base64
import litellm
import html
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, PruningContentFilter
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import json
from urllib.parse import urlparse



# CONFIGURATIONS 
# URL = "https://www.fsdm.usmba.ac.ma"
# URL = "https://www.uca.ma/fr"
# URL = "https://fst-usmba.ac.ma"
URL = "https://www.tawjihnet.net"
# URL = "https://www.tawjihnet.net/inscription-cpge-classes-preparatoires-2025-2026/"

MAX_DEPTH = 1 # Set to 0 for unlimited dept
# MAX_PAGES = 20  # Set to 0 for unlimited dept
SCREENSHOT = True  # Set to True to take screenshots of the pages
PDF= True  # Set to True to generate PDF files of the pages
IFRAMES = False  # Set to True to process iframe content



# CRAWLER CONFIGURATION
crawler_config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=MAX_DEPTH, 
        # max_pages=MAX_PAGES,
        include_external=False
    ),
    # scraping_strategy=LXMLWebScrapingStrategy(),
    verbose=True,
    screenshot=SCREENSHOT,
    pdf=PDF,
    process_iframes=IFRAMES,           # Process iframe content
    cache_mode=CacheMode.BYPASS,  # Enable caching to avoid re-crawling the same pages
    excluded_tags=['form', 'header', 'aside', 'footer', 'nav', 'svg'],  # Exclude certain tags from scraping
    exclude_external_images=True,
    wait_for_images=True,
)


# LITELLM CONFIGURATION



def url_to_filename(url):
    # Remove protocol (http:// or https://)
    url = re.sub(r'^https?://', '', url)
    # Replace non-alphanumeric characters with underscores
    filename = re.sub(r'[^A-Za-z0-9._-]', '_', url)
    return filename


script_dir = os.path.dirname(os.path.abspath(__file__))
hostname = urlparse(URL).hostname
output_dir = os.path.join(script_dir, 'scraped', url_to_filename(hostname))
os.makedirs(output_dir, exist_ok=True) # Creates the folder if it doesn't exist


def filter_links_with_ai(links, prompt, model="deepseek/deepseek-chat", api_key=os.getenv("DEEPSEEK_API_KEY")):
    """
    Given a list of link dicts (with 'text' and 'href'), asks the AI to filter them based on the prompt.
    Returns a list of relevant links.
    """
    # Prepare the list as a string for the LLM, showing all fields
    # If internal_links is a dict of {page_url: [links]}, flatten it
    all_links = []
    for link_list in links.values():
        all_links.extend(link_list)
    links = all_links

    # Remove duplicate links by href
    seen = set()
    unique_links = []
    for link in links:
        href = link.get('href')
        if href and href not in seen:
            unique_links.append(link)
            seen.add(href)
    links = unique_links

    print("\n")
    print("\n")
    print("\n")
    print(f"=========== Links to be filtered by AI: {len(links)} =================")
    print("\n")
    for i, link in enumerate(links, 1):
        print(f"{i}. URL: {link.get('text','')} | {link.get('title','')}  --->> {link.get('href','')}")

    if input(f"Do you want to use the AI to filter {len(links)} links ? (y/n): ").strip().lower() != 'y':
        print("Skipping AI filtering.")
        exit(0)
    
    # Split links into batches of 1000
    batch_size = 500
    filtered_links = []
    for i in range(0, len(links), batch_size):
        batch = links[i:i + batch_size]
        batch_links_str = "\n".join([
            f"TEXT: {link.get('text','')} | TITLE: {link.get('title','')} | URL: {link['href']}"
            for link in batch
        ])
        batch_prompt = (
            f"Given the following list of links (with their text and URLs), "
            f"which ones are most likely to contain information about '{prompt}'?\n"
            "Return only the URLs, one per line, that are plausible sources for this topic.\n\n"
            "Links:\n" + batch_links_str
        )
        response = litellm.completion(
            model=model,
            api_key=api_key,
            messages=[{"role": "user", "content": batch_prompt}],
            max_tokens=512,
            temperature=0.1,
            stream=True,
        )

        print(f"\n====== AI RESPONSE for batch {i//batch_size + 1}: ======")
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content is None:
                print("\n")
            else:
                print(chunk.choices[0].delta.content, end='', flush=True)
                if hasattr(chunk.choices[0], "delta") and hasattr(chunk.choices[0].delta, "content"):
                    full_response += chunk.choices[0].delta.content

        if not full_response.strip():
            print("No valid response from AI for this batch.")
            continue

        # Filter URLs from the AI response based on a regex pattern
        # why regex? because AI responses can be unpredictable and may contain extra text
        url_pattern = r'https?://[^\s)>\]]+'
        # Extract plausible URLs: for each line, if it contains a URL, extract only the URL part
        plausible_urls = []
        for line in full_response.splitlines():
            match = re.search(url_pattern, line)
            if match:
                plausible_urls.append(match.group(0))
        filtered_links.extend([link for link in batch if link['href'] in plausible_urls])

    # Return all filtered links from all batches
    return filtered_links 


async def crawl_and_filter(URL):    

    internal_links = {}  # Dictionary to store internal links for each page

    try:
        async with AsyncWebCrawler() as crawler:
            results = await crawler.arun(URL, config=crawler_config)

            print(f"Crawled {len(results)} pages in total")

            for result in results:
                # Extract only the path from the URL for filename
                page_url = result.url
                path = "index" if urlparse(page_url).path in ('/' or '') else url_to_filename(urlparse(page_url).path)

                # If path is empty (homepage), use 'index'
                filename = (path if path else "index") 

                #create page directory
                page_dir = os.path.join(output_dir, filename)
                os.makedirs(page_dir, exist_ok=True)  # Creates the folder if it doesn't exist
                print(f"Processing page: {page_url} -> {filename}")

                # # write the page to html file
                # with open(f"{page_dir}/raw_html.html", "w", encoding='utf-8') as f:
                #     print("Writing raw HTML to file...")
                #     f.write(result.cleaned_html)
                # with open(f"{page_dir}/cleaned_html.html", "w", encoding='utf-8') as f:
                #     print("Writing cleaned HTML to file...")
                #     f.write(result.cleaned_html)
                # # write markdown file
                # with open(f"{page_dir}/fit_markdown.md", "w", encoding='utf-8') as f:
                #     print("Writing fit markdown to file...")
                #     f.write(result.markdown.fit_markdown)
                # with open(f"{page_dir}/raw_markdown.md", "w", encoding='utf-8') as f:
                #     print("Writing raw markdown to file...")
                #     f.write(result.markdown.raw_markdown)


                # # Media: write image info to JSON file
                # images_info = result.media.get("images", [])
                # print(f"Found {len(images_info)} images in total.")
                # images_file = f"{page_dir}/images.json"
                # with open(images_file, "w", encoding='utf-8') as img_file:
                #     for i, img in enumerate(images_info):  # Inspect just the first 3
                #         print(f"[Image {i}] Found image : {img.get('alt','')}")
                #         # Collect image info in a list of dicts
                #         images_json = []
                #         for i, img in enumerate(images_info):
                #             print(f"[Image {i}] Found image : {img.get('alt','')}")
                #             images_json.append({
                #                 "url": img.get("src"),
                #                 "alt": img.get("alt", ""),
                #                 "score": img.get("score"),
                #                 "description": img.get("desc", "")
                #             })
                #         # Write all image info as JSON
                #         json.dump(images_json, img_file, ensure_ascii=False, indent=2)
                
                # if result.pdf:
                #     print(f"PDF available: {result.pdf is not None}")
                #     with open(f"{page_dir}/document.pdf", "wb") as f:
                #         f.write(result.pdf)
                if result.screenshot:
                    print(f"Screenshot available: {result.screenshot is not None}")
                    with open(f"{page_dir}/screenshot.png", "wb") as f:
                        f.write(base64.b64decode(result.screenshot))
    except Exception as e:
        print(f"An error occurred during crawling: {e}")



        #     exit(0)  # Exit early if you just want to save the HTML files

        # # Access individual results
        # with open(f"{output_dir}/sitemap.xml", "w") as sitemap_file:
        #     for result in results:
        #         # extract values
        #         page_url = result.url            
        #         depth = result.metadata.get('depth', 0)
        #         internal_links[page_url] = result.links.get('internal',[]) 
                
        #         print(f"URL: {page_url} Depth: {depth}")

        #         # Process links
        #         sitemap_file.write(" Depth : " + str(depth) + " : URL : " + page_url + "\n")
        #         for link in result.links.get('internal', []):
        #             # Defensive: check if link is a dict and has 'href'
        #             if not isinstance(link, dict) or 'href' not in link:
        #                 print(f"Warning: Skipping malformed link: {link}")
        #                 continue
        #             if not link['href']:
        #                 print(f"Warning: Link without href found on {page_url}: {link}")
        #                 continue
        #             print(f"Internal link: {link['href']}")
        #             sitemap_file.write("   |__ " + " TEXT : " + link['text'] +" - " + link['title'] + " Link : " + link['href'] + "\n")


        #         # sitemap_file.write(" Depth : " + str(depth) + " : URL : " + page_url + "\n")
        #         if result.screenshot:
        #             print(f"Screenshot available: {result.screenshot is not None}")
        #             screenshot_dir = f"{output_dir}/screenshots"
        #             os.makedirs(screenshot_dir, exist_ok=True)  # Creates the folder if it doesn't exist
        #             with open(f"{screenshot_dir}/ss_{url_to_filename(page_url)}.png", "wb") as f:
        #                 f.write(base64.b64decode(result.screenshot))


if __name__ == "__main__":
    asyncio.run(crawl_and_filter(URL))