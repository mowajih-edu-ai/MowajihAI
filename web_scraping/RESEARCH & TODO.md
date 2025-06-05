

## TODO
* Scrap ALL the URLs with C4AI and then ask AI to filter them
* Screenshot to text ---> OCR!!!!!!!!!
* SCRAPING PROJECT WON'T FORM PART OF THE DEPLOYABLE PACKAGE!!!!! Could I come up with a clever way of automating the scraping process and even ditribute its computation resources on free tiers?

## Brainstorming
* Basic info like what is a Faculty and so on
* Existing websites ARE NOT OUR COMPETITORS. they don'y do assistance, they just post news. WE SHOULD REFERENCE THEM USING RAG.
* our system should start with assistance and NEWS NOTIFICATIONS 
* FOLLOW INSTITUTIONS AND GET NEWS ABOUT THEM
* ALLOSCHOOL: how could we benefit from this website?

## The cost of image-to-text (OCR) in Google AI APIs depends on which API you use and the volume of your usage. Here's a breakdown:

1. Google Cloud Vision API (Text Detection / Document Text Detection)

Free Tier: The first 1,000 units (images) per month are free.
Paid Tier:
Text Detection: After the free tier, it costs $1.50 per 1,000 units for the first 5,000,000 units per month, and then $0.60 per 1,000 units for higher volumes.
Document Text Detection: Similar to Text Detection, it's also $1.50 per 1,000 units for the first 5,000,000 units per month, and then $0.60 per 1,000 units for higher volumes. This is optimized for dense text and documents.

## Few Shots Prompting From Online Communities

## n8n Workflows and sitemaps


## Knowledge Graph Construction (or Access):
### Information Extraction (if needed):
If your sources are unstructured, you'll need to extract entities and relationships.

Techniques include:
- Named Entity Recognition (NER)
- Relation Extraction
- Coreference Resolution
### Graph Schema Definition: 
Define the types of entities and the relationships that can exist between them. 
This helps in structuring your graph effectively.

## Graph Traversal and Retrieval
### Keyword-based Entity Linking:

- Identify keywords in the user query.
- Map these keywords to entities within the knowledge graph.
- Retrieve the neighborhood (connected nodes and edges) of these identified entities.

### Semantic Similarity-based Entity and Relationship Matching:

- Embed the user query into a vector space.
- Embed the names and descriptions of entities and relationships in the same vector space.
- Find entities and relationships with high semantic similarity to the query.
- Retrieve relevant subgraphs connected to these entities/relationships.

### Graph Pattern Matching:
- Translate the user query (or parts of it) into a graph query language (e.g., Cypher for Neo4j, Gremlin for Apache TinkerPop).
- Execute this query on the knowledge graph to find matching patterns or subgraphs.

### Intent Classification
>💡 Maybe we can offer two features in our app. The first is suggest intents to the user, then he clicks and choose what he wants. The second feature is more conversational like a chatbot. The first relies more on the graph. The second one relies more on the LLMs.
> - 🌟 __The conversational feature can also invoke intents when the user intent is clear.__
#### Scaling and diversifying
- AI suggests new intentions at runtime to be added to the available intents
- Train a specialized Intent Classification Model
