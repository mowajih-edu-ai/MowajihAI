import os
import json
import asyncio
from typing import List
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from dotenv import load_dotenv
import litellm
import nest_asyncio

nest_asyncio.apply()

# litellm._turn_on_debug()
load_dotenv('../.env')  # Load environment variables from .env file)
api_key = os.getenv('DEEPSEEK_API_KEY')

if not api_key or not api_key.startswith('sk-'):
    raise ValueError("Invalid or missing DEEPSEEK_API_KEY in .env file")


class Entity(BaseModel):
    name: str
    description: str

class Relationship(BaseModel):
    entity1: Entity
    entity2: Entity
    description: str
    relation_type: str

class KnowledgeGraph(BaseModel):
    entities: List[Entity]
    relationships: List[Relationship]


async def main():

    

    # Step 1: Create a pruning filter
    prune_filter = PruningContentFilter(
            # Lower → more content retained, higher → more content pruned
            threshold=0.45,           
            # "fixed" or "dynamic"
            threshold_type="dynamic",  
            # Ignore nodes with <5 words
            min_word_threshold=5      
        )


    # Step 2: Insert it into a Markdown Generator
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)

    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        # css_selector="ol.product-items",
        excluded_tags=['form', 'header', 'footer', 'nav'],
        cache_mode=CacheMode.BYPASS,
        exclude_external_links=True,
        word_count_threshold=20
    )

    llm_config = LLMConfig( 
                            provider="deepseek/deepseek-chat", 
                            api_token=api_key
                        )

    # LLM extraction strategy
    llm_strat = LLMExtractionStrategy(
        # llmConfig = LLMConfig(provider="gpt-4.1-mini", api_token=os.getenv('OPENAI_API_KEY')),
        llmConfig = llm_config,
        schema=KnowledgeGraph.model_json_schema(),
        extraction_type="schema",
        instruction="Extract entities and relationships from the content. Return valid JSON.",
        chunk_token_threshold=1400,
        apply_chunking=True,
        input_format="html",
        extra_args={"temperature": 0.1, "max_tokens": 1500}
    )

    print("LLM Extraction Strategy:", llm_strat.llm_config.provider, llm_strat.llm_config.api_token)

    crawl_config = CrawlerRunConfig(
        extraction_strategy=llm_strat,
        markdown_generator=md_generator,
        cache_mode=CacheMode.BYPASS
    )

    proceed = input('proceed?:')

    if proceed != 'y':
        return


    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.tawjihnet.net/bac-concours-licence-iscae-casa-2025-2026", 
            config=config
        )
        
        print("images:", result[0].media.get('images', [])[0]['src'])
        final_result = result.markdown.fit_markdown
        length = len(final_result)
        print("Partial HTML length:", len(final_result))
        with open("kb_result.md", "w", encoding="utf-8") as f:
            f.write(final_result)
        print("HTML Content: ========================")
        # print(final_result)

        print("provider:",llm_strat.llm_config.provider)
        print("API KEY:",llm_strat.llm_config.api_token)
        print("LLM Extraction Strategy:", llm_strat.llm_config.provider, llm_strat.llm_config.api_token)

        proceed = input("Length is: [[ " + str(length) + " characters ]] proceed?:")
        if proceed != 'y':
            return

        if length > 10000:
            print("STOP EXTRACTION...")
            exit(0)

        # Example page
        url = "https://www.tawjihnet.net/bac-concours-licence-iscae-casa-2025-2026"
        result = await crawler.arun(url=url, config=crawl_config)


        if result.success:
            with open("kb_result.json", "w", encoding="utf-8") as f:
                f.write(result.extracted_content)
                print(result.extracted_content)
            llm_strat.show_usage()
        else:
            print("Crawl failed:", result.error_message)




if __name__ == "__main__":
    asyncio.run(main())
