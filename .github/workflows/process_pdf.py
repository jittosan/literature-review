import os
import re
import PyPDF2
import markdown
from pathlib import Path

# Path to the README and PDF directory
README_PATH = 'README.md'
PDF_DIR = '.'

# Function to extract metadata (e.g., title) from the PDF
def extract_title_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfFileReader(f)
            if reader.isEncrypted:
                reader.decrypt('')
            # Try extracting the title from the document information metadata
            title = reader.getDocumentInfo().title
            if title:
                return title
            # If no title is found, fall back to a generic name
            return os.path.basename(pdf_path).replace('.pdf', '')
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return None

# Function to rename PDF files to their title
def rename_pdf(pdf_path, title):
    new_filename = re.sub(r'[\\/*?:"<>|]', "", title) + ".pdf"
    new_filepath = os.path.join(PDF_DIR, new_filename)
    os.rename(pdf_path, new_filepath)
    return new_filepath

# Function to update the README.md file with a table of all PDFs
def update_readme():
    readme_content = "# Papers in the Repository\n\n"
    readme_content += "| Title | Filename |\n"
    readme_content += "|-------|----------|\n"
    
    for file in Path(PDF_DIR).glob("*.pdf"):
        title = extract_title_from_pdf(file)
        if title:
            new_file_path = rename_pdf(file, title)
            readme_content += f"| {title} | [{new_file_path}](./{new_file_path}) |\n"
    
    with open(README_PATH, 'w') as readme_file:
        readme_file.write(readme_content)

if __name__ == "__main__":
    update_readme()
