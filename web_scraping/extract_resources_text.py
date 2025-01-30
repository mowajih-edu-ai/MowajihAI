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
            
            text = pytesseract.image_to_string(Image.open(img_byte_array), lang='eng')  # Changez 'eng' en 'fra' pour le français
            
            text_file.write(f"--- Page {page_num} ---\n")
            text_file.write(text)
            text_file.write("\n\n")
    
    print(f"Texte extrait de {pdf_file} et enregistré dans {text_filename}")

print("Extraction terminée pour tous les fichiers PDF.")
