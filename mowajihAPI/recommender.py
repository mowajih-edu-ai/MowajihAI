import os
import json
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from langchain.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone
from flask_cors import CORS 

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get Pinecone API Key
pinecone_api_key = os.getenv('PINECONE_API_KEY')

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

def download_hugging_face_embeddings():
    """Load Hugging Face embeddings model."""
    logging.info("Downloading Hugging Face embeddings model...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    logging.info("Hugging Face embeddings model loaded successfully.")
    return embeddings

embeddings = download_hugging_face_embeddings()

def get_embedding(text):
    """Get the embedding for the given text using Hugging Face embeddings."""
    try:
        logging.info(f"Generating embedding for text: {text[:50]}...")  # Show first 50 characters
        embedding = embeddings.embed_query(text)
        logging.info("Embedding generated successfully.")
        return embedding
    except Exception as e:
        logging.error(f"Error generating embedding: {e}")
        return None

def initialize_pinecone():
    """Initialize Pinecone and access the existing index."""
    try:
        logging.info("Initializing Pinecone...")
        pc = Pinecone(api_key=pinecone_api_key)
        index_name = "university-programs"
        index = pc.Index(index_name)
        logging.info("Pinecone initialized successfully and index accessed.")
        return index
    except Exception as e:
        logging.error(f"Error initializing Pinecone: {e}")
        return None

@app.route('/recommend', methods=['POST'])
def recommend_program():
    """Flask endpoint to recommend top 3 university programs based on user input."""
    try:
        # Log the received request
        logging.info("Received recommendation request.")
        user_data = request.json
        logging.info(f"Request JSON: {json.dumps(user_data, indent=2)}")  # Pretty print JSON

        user_responses = user_data.get("answers", [])
        if not user_responses:
            logging.warning("No answers provided in the request.")
            return jsonify({"error": "No answers provided"}), 400

        # Construct user profile
        logging.info("Constructing user profile from responses...")
        user_profile = construct_user_profile(user_responses)
        logging.info(f"Constructed user profile: {user_profile}")

        # Initialize Pinecone index
        index = initialize_pinecone()
        if not index:
            logging.error("Failed to initialize Pinecone index.")
            return jsonify({"error": "Failed to initialize Pinecone index"}), 500

        # Generate query embedding
        query_embedding = get_embedding(user_profile)
        if query_embedding is None:
            logging.error("Failed to generate embedding for the user profile.")
            return jsonify({"error": "Embedding generation failed"}), 500

        # Query Pinecone for recommendations
        logging.info("Querying Pinecone for recommendations...")
        results = index.query(vector=query_embedding, top_k=3, include_metadata=True)

        # Process results
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

        logging.info(f"Successfully retrieved {len(recommendations)} recommendations.")
        return jsonify({'recommendations': recommendations})

    except Exception as e:
        logging.error(f"Error during recommendation process: {e}")
        return jsonify({"error": "Failed to process the recommendation"}), 500

def construct_user_profile(answers):
    """Converts structured JSON answers into a human-readable profile description."""
    try:
        logging.info("Constructing a human-readable profile from answers...")
        profile_parts = [f"{answer.get('question')} {answer.get('answer')}." for answer in answers if answer.get("question") and answer.get("answer")]
        constructed_profile = " ".join(profile_parts)
        logging.info("User profile constructed successfully.")
        return constructed_profile
    except Exception as e:
        logging.error(f"Error constructing user profile: {e}")
        return ""

if __name__ == '__main__':
    logging.info("Starting Flask server...")
    app.run(debug=True, port=5000)
