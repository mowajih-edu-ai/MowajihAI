# University Programs Processing Workflow

This project automates the extraction, structuring, and storage of university program details from PDF documents using AI-driven techniques.

## Workflow Overview

The process consists of four main steps:

### 1️⃣ Download Resources

- Automatically download **PDF documents** describing various **university programs** (Bachelor, Master, etc.) from the official university website.
- The following Python script scrapes and downloads PDFs from [FST Fes](https://fst-usmba.ac.ma/formation-initiale-fst-fes/):
  ```python
  import requests
  from bs4 import BeautifulSoup
  import os

  output_directory = "pdf_fst_fes"
  if not os.path.exists(output_directory):
      os.makedirs(output_directory)

  url = "https://fst-usmba.ac.ma/formation-initiale-fst-fes/"
  response = requests.get(url)
  soup = BeautifulSoup(response.content, "html.parser")

  pdf_links = soup.find_all("a", href=True)
  for link in pdf_links:
      href = link['href']
      if "framework/uploads" in href and href.endswith('.pdf'):
          pdf_url = href if href.startswith("http") else f"https://fst-usmba.ac.ma{href}"
          pdf_response = requests.get(pdf_url)
          filename = os.path.join(output_directory, pdf_url.split("/")[-1])
          with open(filename, 'wb') as pdf_file:
              pdf_file.write(pdf_response.content)
          print(f"PDF téléchargé : {filename}")
  ```

### 2️⃣ Extract Text from PDFs

- Convert PDFs, including **image-based PDFs**, into machine-readable text.
- Use **OCR (Optical Character Recognition)** to extract text.
- The following Python script extracts text from the downloaded PDFs:
  ```python
  import os
  import io
  from pdf2image import convert_from_path
  import pytesseract
  from PIL import Image

  pdf_fst_fes_dir = 'pdf_fst_fes'
  text_output_dir = 'text_extracted'

  os.makedirs(text_output_dir, exist_ok=True)

  pdf_files = [f for f in os.listdir(pdf_fst_fes_dir) if f.endswith('.pdf')]

  for pdf_file in pdf_files:

      pdf_path = os.path.join(pdf_fst_fes_dir, pdf_file)
      
      pages = convert_from_path(pdf_path, dpi=300, fmt="jpeg")
      
      text_filename = os.path.join(text_output_dir, f"{os.path.splitext(pdf_file)[0]}_extracted_text.txt")
      
      with open(text_filename, 'w', encoding='utf-8') as text_file:
          for page_num, page in enumerate(pages, start=1):

              img_byte_array = io.BytesIO()
              page.save(img_byte_array, 'JPEG')
              img_byte_array.seek(0)
              
              text = pytesseract.image_to_string(Image.open(img_byte_array), lang='eng')  # Change 'eng' to 'fra' for French
              
              text_file.write(f"--- Page {page_num} ---\n")
              text_file.write(text)
              text_file.write("\n\n")
      
      print(f"Texte extrait de {pdf_file} et enregistré dans {text_filename}")

  print("Extraction terminée pour tous les fichiers PDF.")
  ```

### 3️⃣ Extract Structured Data Using LLMs

- Process extracted text with **Large Language Models (LLMs)** to structure information.
- Uses **OpenAI's GPT model** for text extraction and formatting.
- Logs processing activities using Python's **logging** module.
- Outputs a **JSON object** containing structured details such as title, description, opportunities, and acces**s** conditions.
- Ensures proper handling of file reading errors and JSON conversion issues.

### 4️⃣ Store Vector Embeddings in a Vector Database

- Generate **vector embeddings** from extracted text using LLMs (OpenAI).
- Store embeddings in a **Vector Database** for efficient semantic search and retrieval.
- Database used:
  - **[Pinecone](https://www.pinecone.io/)**


## Usage

Run the script to : 

1. Download PDFs.
2. Extract text from PDFs.
3. Process extracted text with an LLM.
4. Store embeddings in a vector database.

## License

This project is licensed under the MIT License.

---

🚀 **Happy Coding!**

