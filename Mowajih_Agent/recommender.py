import os
import json
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from langchain.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

pinecone_api_key = os.getenv('PINECONE_API_KEY')

app = Flask(__name__)

def download_hugging_face_embeddings():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return embeddings

embeddings = download_hugging_face_embeddings()

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
    Initialize Pinecone and access the existing index.
    """
    try:
        pc = Pinecone(api_key=pinecone_api_key)
        index_name = "university-programs"
        index = pc.Index(index_name)
        return index
    except Exception as e:
        logging.error(f"Error initializing Pinecone: {e}")
        return None

@app.route('/recommend', methods=['POST'])
def recommend_program():
    """
    Flask endpoint to recommend top 3 university programs based on user input.
    """
    user_input = request.json.get('user_input')
    if not user_input:
        return jsonify({"error": "User input is required"}), 400

    index = initialize_pinecone()
    if not index:
        return jsonify({"error": "Failed to initialize Pinecone index"}), 500

    try:
        query_embedding = get_embedding(user_input)

        results = index.query(vector=query_embedding, top_k=3, include_metadata=True)

        recommendations = []
        for match in results['matches']:
            metadata = match.get('metadata', {})
            recommendations.append({
                'title': metadata.get('title', 'Unknown Title'),
                'description': metadata.get('description', 'No description available'),
                'opportunities': metadata.get('opportunities', []),
                'access_conditions': metadata.get('access_conditions', 'No access conditions provided'),
                'score': match.get('score', 0)
            })

        return jsonify({'recommendations': recommendations})

    except Exception as e:
        logging.error(f"Error during recommendation: {e}")
        return jsonify({"error": "Failed to process the recommendation"}), 500

if __name__ == '__main__':
    app.run(debug=True)
