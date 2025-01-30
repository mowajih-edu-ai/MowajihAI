import os
import json
import logging
from dotenv import load_dotenv
import uuid
from langchain.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone
from pinecone import ServerlessSpec

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

pinecone_api_key = os.getenv('PINECONE_API_KEY')

university_programs_dir = 'universityprograms'
programs_data = []

def download_hugging_face_embeddings():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return embeddings

embeddings = download_hugging_face_embeddings()

def load_programs():
    """
    Load all JSON files from the university programs directory.
    """
    global programs_data
    programs_data = []
    for json_file in os.listdir(university_programs_dir):
        if json_file.endswith('.json'):
            try:
                with open(os.path.join(university_programs_dir, json_file), 'r') as f:
                    program_info = json.load(f)
                    programs_data.append(program_info)
                logging.info(f"Loaded {json_file} successfully.")
            except Exception as e:
                logging.error(f"Error loading {json_file}: {e}")

def get_embedding(text):
    """
    Get the embedding for the given text using Hugging Face embeddings.
    """
    try:
        embedding = embeddings.embed_query(text)
        return embedding
    except Exception as e:
        logging.error(f"Error getting embedding for text: {e}")
        return None

def initialize_pinecone():
    """
    Initialize Pinecone and create the index if it doesn't exist.
    """
    try:
        pc = Pinecone(api_key=pinecone_api_key)
        
        index_name = "university-programs"

        index = pc.Index(index_name)
        return index
    
    except Exception as e:
        logging.error(f"Error initializing Pinecone: {e}")
        return None

def vectorize_and_store_programs(index):
    """
    Vectorize all programs and store the embeddings in Pinecone.
    """
    try:
        for program in programs_data:
            # Generate a unique ID if not present
            program_id = program.get('id', str(uuid.uuid4()))
            title = program.get('title', 'Unknown Title')
            description = program.get('description', 'No description available')
            opportunities = program.get('opportunities', [])
            access_conditions = program.get('access_conditions', 'No access conditions provided')

            combined_text = f"{title} {description} {opportunities} {access_conditions}".strip()

            embedding = get_embedding(combined_text)

            if embedding:
                # Ensure metadata is complete before upserting
                metadata = {
                    'title': title,
                    'description': description,
                    'opportunities': opportunities,
                    'access_conditions': access_conditions
                }

                index.upsert(
                    vectors=[{
                        'id': program_id,
                        'values': embedding,
                        'metadata': metadata
                    }]
                )
                logging.info(f"Stored embedding for program : {title} with ID: {program_id}")
            else:
                logging.error(f"Failed to get embedding for program: {title}")
    except Exception as e:
        logging.error(f"Error during vectorization or storing: {e}")

def main():
    """
    Main function to load programs, vectorize them, and store them in Pinecone.
    """
    logging.info("Starting the process of loading and storing programs.")
    load_programs()

    if not programs_data:
        logging.error("No programs loaded. Please check the directory and JSON files.")
        return

    index = initialize_pinecone()

    if index:
        vectorize_and_store_programs(index)
        logging.info("Process completed successfully.")
    else:
        logging.error("Failed to initialize Pinecone, process aborted.")

if __name__ == '__main__':
    main()
