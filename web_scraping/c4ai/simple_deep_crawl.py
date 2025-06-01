
import asyncio
import re
import os
import base64
import litellm
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

# CONFIGURATIONS 
# URL = "https://www.fsdm.usmba.ac.ma/"
URL = "https://fst-usmba.ac.ma/"
# URL = "https://www.tawjihnet.net/"

MAX_DEPTH = 0 # Set to 0 for unlimited dept
MAX_PAGES = 20  # Set to 0 for unlimited dept
SCREENSHOT = False  # Set to True to take screenshots of the pages
IFRAMES = False  # Set to True to process iframe content

# CRAWLER CONFIGURATION
crawler_config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=MAX_DEPTH, 
        max_pages=MAX_PAGES,
        include_external=False
    ),
    scraping_strategy=LXMLWebScrapingStrategy(),
    verbose=True,
    screenshot=SCREENSHOT,
    process_iframes=IFRAMES,           # Process iframe content
)


# LITELLM CONFIGURATION



def url_to_filename(url):
    # Remove protocol (http:// or https://)
    url = re.sub(r'^https?://', '', url)
    # Replace non-alphanumeric characters with underscores
    filename = re.sub(r'[^A-Za-z0-9._-]', '_', url)
    return filename


script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, 'scraped', url_to_filename(URL))
os.makedirs(output_dir, exist_ok=True) # Creates the folder if it doesn't exist


def filter_links_with_ai(links, prompt, model="deepseek/deepseek-chat", api_key=os.getenv("DEEPSEEK_API_KEY")):
    """
    Given a list of link dicts (with 'text' and 'href'), asks the AI to filter them based on the prompt.
    Returns a list of relevant links.
    """
    # Prepare the list as a string for the LLM, showing all fields
    # If internal_links is a dict of {page_url: [links]}, flatten it
    if isinstance(links, dict):
        all_links = []
        for link_list in links.values():
            all_links.extend(link_list)
        links = all_links

    links_str = "\n".join([
        f"TEXT: {link.get('text','')} | TITLE: {link.get('title','')} | URL: {link['href']}"
        for link in links
    ])

    print(f"Links to be filtered by AI: {len(links)}")
    for link in links:
        print(f"TEXT: {link.get('text','')} | TITLE: {link.get('title','')} | URL: {link['href']}")

    if input(f"Do you want to use the AI to filter {len(links)} links ? (y/n): ").strip().lower() != 'y':
        print("Skipping AI filtering.")
        exit(0)

    user_prompt = (
        f"Given the following list of links (with their text and URLs), "
        f"which ones are most likely to contain information about '{prompt}'?\n"
        "Return only the URLs, one per line, that are plausible sources for this topic.\n\n"
        "Links:\n" + links_str
    )

    response = litellm.completion(
        model=model,
        api_key=api_key,
        messages=[{"role": "user", "content": user_prompt}],
        max_tokens=512,
        temperature=0.1,
    )
    
    # log ai respon
    print(" ====== AI RESPONSE: ======")
    if not response or 'choices' not in response or not response['choices']:
        print("No valid response from AI.")
        return []
    print(response['choices'][0]['message']['content'])

    # Extract URLs from the response (one per line)
    plausible_urls = [
        line.strip() for line in response['choices'][0]['message']['content'].splitlines()
        if line.strip().startswith("http")
    ]

    # Optionally, return the full link dicts for those URLs
    return [link for link in links if link['href'] in plausible_urls]




async def main():    

    internal_links = {}  # Dictionary to store internal links for each page

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(URL, config=crawler_config)

        print(f"Crawled {len(results)} pages in total")

        # Access individual results
        with open(f"{output_dir}/sitemap.xml", "w") as sitemap_file:
            for result in results:
                # extract values
                page_url = result.url            
                depth = result.metadata.get('depth', 0)
                
                print(f"URL: {page_url} Depth: {depth}")

                # Process links
                sitemap_file.write(" Depth : " + str(depth) + " : URL : " + page_url + "\n")
                for link in result.links["internal"]:
                    print(f"Internal link: {link['href']}")
                    sitemap_file.write("   |__ " + " TEXT : " + link['text'] +" - " + link['title'] + " Link : " + link['href'] + "\n")


                # sitemap_file.write(" Depth : " + str(depth) + " : URL : " + page_url + "\n")
                if result.screenshot:
                    print(f"Screenshot available: {result.screenshot is not None}")
                    screenshot_dir = f"{output_dir}/screenshots"
                    os.makedirs(screenshot_dir, exist_ok=True)  # Creates the folder if it doesn't exist
                    with open(f"{screenshot_dir}/ss_{url_to_filename(page_url)}.png", "wb") as f:
                        f.write(base64.b64decode(result.screenshot))

                internal_links[page_url] = result.links['internal'] 
            
            filtered_links = filter_links_with_ai(
                internal_links,
                "formations et programmes de formation",
            )

            # print total number of filtered links
            print(f"============================ filtered links: {len(filtered_links)} ==================="+"\n")

            sitemap_file.write("\n")
            sitemap_file.write("\n")
            sitemap_file.write("\n")
            sitemap_file.write(f"============================ filtered links: {len(filtered_links)} ==================="+"\n")
            for link in filtered_links:
                print(f"Filtered link: {link['text']} - {link['href']}")
                sitemap_file.write(f"Filtered link: {link['text']} - {link['href']}\n")


if __name__ == "__main__":
    asyncio.run(main())