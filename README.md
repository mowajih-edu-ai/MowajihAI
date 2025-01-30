# University Programs Processing Workflow

This project automates the extraction, structuring, and storage of university program details from PDF documents using AI-driven techniques.

## Workflow Overview

The process consists of four main steps:

### 1️⃣ Download Resources

- Retrieve PDF documents describing various **university programs** (Bachelor, Master, etc.).
- These PDFs may contain structured text or be image-based (scanned documents).

### 2️⃣ Extract Text from PDFs

- Convert PDFs, including **image-based PDFs**, into machine-readable text.
- Use **OCR (Optical Character Recognition)** tools like:
  - [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
  - [pdfplumber](https://github.com/jsvine/pdfplumber)
  - [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/en/latest/)

### 3️⃣ Extract Structured Data Using LLMs

- Process extracted text with **Large Language Models (LLMs)** to structure information.
- Output is a **JSON object** containing:
  ```json
  {
    "university": "Example University",
    "degree": "Master",
    "program": "Artificial Intelligence",
    "duration": "2 years",
    "credits": 120,
    "language": "English"
  }
  ```

### 4️⃣ Store Vector Embeddings in a Vector Database

- Generate **vector embeddings** from extracted text using LLMs (e.g., OpenAI, Hugging Face).
- Store embeddings in a **Vector Database** for efficient semantic search and retrieval.
- Possible databases:
  - [**Pinecone**](https://www.pinecone.io/)
  - [**Weaviate**](https://weaviate.io/)
  - [**FAISS**](https://github.com/facebookresearch/faiss)

## Installation & Setup

To run this workflow, ensure you have:

- Python **3.x** installed.
- Required dependencies:
  ```sh
  pip install tesseract pdfplumber pymupdf openai pinecone-client
  ```
- API keys for LLM and vector database services (if applicable).

## Usage

1. Run the script to download PDFs.
2. Extract text from PDFs.
3. Process extracted text with an LLM.
4. Store embeddings in a vector database.

## Future Improvements

- Implement a **web interface** for uploading and processing PDFs.
- Improve **data validation** and **error handling**.
- Optimize **vector search retrieval** for better performance.

## License

This project is licensed under the MIT License.

---

🚀 **Happy Coding!**

