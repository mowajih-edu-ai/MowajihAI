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
