import os
import glob
import re
import requests
from PyPDF2 import PdfReader

# Function to extract DOI and Title from PDF
def extract_metadata(pdf_path):
    reader = PdfReader(pdf_path)
    title = reader.metadata.title if reader.metadata and reader.metadata.title else None
    text = ""
    for page in reader.pages[:5]:  # Read the first 5 pages to find DOI
        text += page.extract_text() or ""
    doi_match = re.search(r'\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b', text, re.I)
    doi = doi_match.group(0) if doi_match else None
    return title, doi

# Function to fetch metadata from CrossRef API
def fetch_crossref_metadata(doi):
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['message']
    return None

# Update main README.md
def update_main_readme(categories):
    readme_content = """# Paper Organizer

This repository helps organize and manage scientific paper PDFs for various research projects.

## Objectives

- Automate the organization of PDFs into categories.
- Extract metadata from PDFs.
- Maintain an updated list of papers with quick access.

## Categories

The following categories are available:

| Category Name | Description |
|---------------|-------------|
"""
    for category in sorted(categories):
        readme_content += f"| [{category}]({category}/) | Description of {category} |\n"

    with open('README.md', 'w') as f:
        f.write(readme_content)

# Iterate over PDFs in sub-directories
def organize_papers():
    categories = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')]
    update_main_readme(categories)
    for category in categories:
        pdf_files = glob.glob(f"{category}/*.pdf")
        if not pdf_files:
            continue
        readme_path = os.path.join(category, 'README.md')
        papers_info = []
        for pdf_file in pdf_files:
            print(f"Processing {pdf_file}")
            title, doi = extract_metadata(pdf_file)
            metadata = None
            if doi:
                metadata = fetch_crossref_metadata(doi)
            if metadata:
                title = metadata.get('title', [title])[0] if metadata.get('title') else title
                authors = ', '.join([author.get('family', '') for author in metadata.get('author', [])])
                journal = metadata.get('container-title', [''])[0]
                year = metadata.get('published-print', {}).get('date-parts', [[None]])[0][0]
            else:
                authors = journal = year = ''
            if not title:
                title = os.path.splitext(os.path.basename(pdf_file))[0]
            # Rename PDF to the paper title
            safe_title = title.replace('/', '-').replace('\\', '-').replace(':', '-')
            new_pdf_path = os.path.join(category, f"{safe_title}.pdf")
            if pdf_file != new_pdf_path:
                os.rename(pdf_file, new_pdf_path)
            # Collect paper info
            papers_info.append({
                'title': title,
                'authors': authors,
                'journal': journal,
                'year': year,
                'pdf_path': os.path.basename(new_pdf_path)
            })
        # Update README.md in the category folder
        with open(readme_path, 'w') as readme_file:
            readme_file.write(f"# Papers in {category}\n\n")
            if papers_info:
                readme_file.write("| Title | Authors | Journal | Year |\n")
                readme_file.write("|-------|---------|---------|------|\n")
                for info in papers_info:
                    title_link = f"[{info['title']}]({info['pdf_path']})"
                    readme_file.write(f"| {title_link} | {info['authors']} | {info['journal']} | {info['year']} |\n")
            else:
                readme_file.write("No papers found in this category.\n")

if __name__ == "__main__":
    organize_papers()
