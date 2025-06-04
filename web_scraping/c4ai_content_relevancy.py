import asyncio
from crawl4ai.deep_crawling.filters import ContentRelevanceFilter
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeepCrawlStrategy, FilterChain, LXMLWebScrapingStrategy, CacheMode


async def main():
    """
    PART 4: Demonstrates advanced filtering techniques for specialized crawling.

    This function covers:
    - SEO filters
    - Text relevancy filtering
    - Combining advanced filters
    """
    print("\n===== ADVANCED FILTERS =====")

    async with AsyncWebCrawler() as crawler:
        print("\n📊 EXAMPLE 2: ADVANCED TEXT RELEVANCY FILTER")

        # More sophisticated content relevance filter
        relevance_filter = ContentRelevanceFilter(
            query="le sérieux est la clé de voûte d’une approche intégrée qui subordonne l’exercice de la responsabilité à l’exigence de reddition des comptes et fait prévaloir les règles de bonne gouvernance, la valeur travail, le mérite et l’égalité des chances",
            threshold=0.9,
        )

        config = CrawlerRunConfig(
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_depth=2, max_pages=50, filter_chain=FilterChain([relevance_filter])
            ),
            scraping_strategy=LXMLWebScrapingStrategy(),
            verbose=True,
            cache_mode=CacheMode.BYPASS,
        )

        results = await crawler.arun(url="https://www.fsdm.usmba.ac.ma/", config=config)

        print(f"  ✅ Found {len(results)} pages")
        for result in results:
            relevance_score = result.metadata.get("relevance_score")
            print(f"  → Score: {relevance_score:.2f} | {result.url}")

asyncio.run(main())