import openai
import json
import os
import logging

# Configure OpenAI API key
openai.api_key =  os.getenv('OPENAI_API_KEY')

# Set up logging
logging.basicConfig(
    level=logging.INFO,  # Log info and above levels
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("program_extraction.log"),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

# Répertoire contenant les fichiers texte extraits
text_extracted_dir = 'text_extracted'
# Répertoire pour stocker les fichiers JSON extraits
university_programs_dir = 'universityprograms'

# Créer le répertoire universityprograms s'il n'existe pas
os.makedirs(university_programs_dir, exist_ok=True)

# Fonction pour lire le contenu des fichiers texte
def read_text_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return None

# Fonction pour appeler le modèle LLM et extraire les informations sous forme de JSON
def extract_program_info_from_text(text):
    prompt = f"""
    You are an AI assistant tasked with extracting structured information about university programs from a text. 
    Extract the following details: 
    - Title: The name of the program or course.
    - Description: A brief description of the program or course.
    - Opportunities: A list of professional work areas or job titles a student could pursue after completing this program. Each job title should be listed as a string.
    - Access Conditions: The entry requirements for the program (e.g., prerequisites, qualifications, or other conditions for admission).

    Return the information as a JSON object with the format:
    {{
        "title": "<Program Title>",
        "description": "<Program Description>",
        "opportunities": ["<Opportunity 1>", "<Opportunity 2>", "<Opportunity 3>"],
        "access_conditions": "<Access Conditions>"
    }}
    
    Here's the text:
    {text}
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # You can use a different model if needed
            messages=[
                {"role": "system", "content": "You are an assistant that extracts information from university programs."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.5
        )
        # Extract and return the JSON response
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Error during OpenAI API call: {e}")
        return None

# Traitement de tous les fichiers texte dans le répertoire text_extracted
for text_file in os.listdir(text_extracted_dir):
    if text_file.endswith('.txt'):
        logging.info(f"Processing file: {text_file}")

        # Lire le texte du fichier
        text_file_path = os.path.join(text_extracted_dir, text_file)
        text = read_text_file(text_file_path)
        
        if text is None:
            logging.warning(f"Skipping file {text_file} due to read error.")
            continue
        
        # Extraire les informations structurées du texte
        program_info_json = extract_program_info_from_text(text)
        
        if program_info_json is None:
            logging.warning(f"Skipping file {text_file} due to extraction failure.")
            continue
        
        # Tenter de parser la réponse comme un objet JSON
        try:
            program_info = json.loads(program_info_json)
            
            # Sauvegarder le résultat dans un fichier JSON dans le répertoire universityprograms
            output_json_path = os.path.join(university_programs_dir, f"{os.path.splitext(text_file)[0]}_program_info.json")
            with open(output_json_path, 'w', encoding='utf-8') as json_file:
                json.dump(program_info, json_file, indent=4, ensure_ascii=False)
            
            logging.info(f"Program info extracted for {text_file} and saved in universityprograms directory.")
        
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error for {text_file}: {e}")
            continue

logging.info("Extraction of program info complete for all text files.")
