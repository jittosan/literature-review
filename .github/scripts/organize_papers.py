import os
import glob
import re
import requests
from PyPDF2 import PdfReader
from urllib.parse import quote

# Function to extract DOI and Title from PDF
def extract_metadata(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        title = reader.metadata.title if reader.metadata and reader.metadata.title else None
        text = ""
        for page in reader.pages[:5]:  # Read the first 5 pages to find DOI
            page_text = page.extract_text()
            if page_text:
                text += page_text
        doi_match = re.search(r'\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b', text, re.I)
        doi = doi_match.group(0) if doi_match else None
        return title, doi
    except Exception as e:
        print(f"Error extracting metadata from {pdf_path}: {e}")
        return None, None

# Function to fetch metadata from CrossRef API
def fetch_crossref_metadata(doi):
    try:
        url = f"https://api.crossref.org/works/{doi}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['message']
        else:
            print(f"Failed to fetch metadata for DOI {doi}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching CrossRef metadata for DOI {doi}: {e}")
        return None

# Function to update a section between start and end markers
def update_section(readme_path, start_marker, end_marker, new_content):
    if not os.path.exists(readme_path):
        print(f"README file {readme_path} does not exist. Creating a new one with default content.")
        with open(readme_path, 'w') as f:
            # Initialize README with a header
            header = f"# {os.path.basename(os.path.dirname(readme_path))}\n\n"
            f.write(header)
            # Insert the new content if provided
            if new_content:
                f.write(new_content)
        return

    with open(readme_path, 'r') as f:
        content = f.read()

    # Regex to find content between markers
    pattern = re.compile(
        f"({re.escape(start_marker)})(.*?)(\n?{re.escape(end_marker)})",
        re.DOTALL
    )

    if new_content:
        # New content with markers
        new_section = f"{start_marker}\n{new_content}\n{end_marker}"
        if pattern.search(content):
            # Replace existing section
            updated_content = pattern.sub(new_section, content)
        else:
            # If markers not found, append the new section
            updated_content = content.strip() + "\n\n" + new_section
    else:
        # If no content provided, remove the section between markers
        updated_content = pattern.sub("", content)
        # Clean up any extra newlines introduced
        updated_content = re.sub(r'\n{3,}', '\n\n', updated_content).strip()

    with open(readme_path, 'w') as f:
        # Add a newline at the end if content exists
        f.write(updated_content + "\n" if updated_content else "")

# Function to create default README.md with markers
def create_default_readme(readme_path):
    default_content = ""
    # Check if the directory is the root or a subdirectory
    dir_name = os.path.basename(os.path.dirname(readme_path))
    default_content += f"# {dir_name}\n\n"
    default_content += "Description for " + dir_name + ".\n\n"

    # Initialize Subcategories section
    subcat_start = '<!-- SUBCATEGORIES_SECTION_START -->'
    subcat_end = '<!-- SUBCATEGORIES_SECTION_END -->'
    default_content += f"{subcat_start}\n"
    default_content += "## Subcategories\n\n"
    default_content += "| Subcategory Name | Description |\n|------------------|-------------|\n"
    default_content += "| [Sub Category A](Sub%20Category%20A/) | Description of Sub Category A |\n"
    default_content += "| [Sub Category B](Sub%20Category%20B/) | Description of Sub Category B |\n"
    default_content += f"{subcat_end}\n\n"

    # Initialize Papers section
    papers_start = '<!-- PAPERS_TABLE_START -->'
    papers_end = '<!-- PAPERS_TABLE_END -->'
    default_content += f"{papers_start}\n"
    default_content += "## Papers\n\n"
    default_content += "| Title | Authors | Journal | Year |\n|-------|---------|---------|------|\n"
    default_content += "| [Sample Paper Title](Sample_Paper_Title.pdf) | Author A, Author B | [Journal Name](https://journal-url.com) | 2023 |\n"
    default_content += f"{papers_end}\n"

    with open(readme_path, 'w') as f:
        f.write(default_content)
    print(f"Created default README.md at {readme_path}")

# Function to update the main README.md with categories
def update_main_readme(categories):
    main_readme = 'README.md'
    start_marker = '<!-- CATEGORIES_TABLE_START -->'
    end_marker = '<!-- CATEGORIES_TABLE_END -->'

    table_header = "| Category Name | Description |\n|---------------|-------------|"
    table_rows = ""
    for category in sorted(categories):
        # URL-encode the category name for the link
        category_link = quote(category) + '/'
        table_rows += f"| [{category}]({category_link}) | Description of {category} |\n"

    new_table = f"{table_header}\n{table_rows}"
    update_section(main_readme, start_marker, end_marker, new_table)

# Function to create or update a subdirectory README.md
def create_or_update_sub_readme(current_dir, subdirectories, papers_info):
    readme_path = os.path.join(current_dir, 'README.md')
    
    # If README.md does not exist, create it with default content
    if not os.path.exists(readme_path):
        create_default_readme(readme_path)
    
    # Define markers for subcategories and papers sections
    subcat_start = '<!-- SUBCATEGORIES_SECTION_START -->'
    subcat_end = '<!-- SUBCATEGORIES_SECTION_END -->'
    papers_start = '<!-- PAPERS_TABLE_START -->'
    papers_end = '<!-- PAPERS_TABLE_END -->'

    # Create Subcategories Section Content (only if subdirectories exist)
    if subdirectories:
        subcat_header = "## Subcategories\n\n"
        subcat_table_header = "| Subcategory Name | Description |\n|------------------|-------------|"
        subcat_rows = ""
        for sub in sorted(subdirectories):
            sub_link = quote(sub) + '/'
            subcat_rows += f"| [{sub}]({sub_link}) | Description of {sub} |\n"
        subcat_content = f"{subcat_header}{subcat_table_header}\n{subcat_rows}"
    else:
        subcat_content = ""  # No subcategories, so no content

    # Create Papers Table Content
    if papers_info:
        papers_header = "## Papers\n\n"
        papers_table_header = "| Title | Authors | Journal | Year |\n|-------|---------|---------|------|"
        papers_rows = ""
        for info in papers_info:
            # URL-encode the PDF path for the link
            pdf_url = quote(info['pdf_path'])
            title_link = f"[{info['title']}]({pdf_url})"
            # Journal as a link to the published paper's URL
            if info['journal_url']:
                journal_link = f"[{info['journal']}]({info['journal_url']})"
            else:
                journal_link = info['journal']
            papers_rows += f"| {title_link} | {info['authors']} | {journal_link} | {info['year']} |\n"
        papers_content = f"{papers_header}{papers_table_header}\n{papers_rows}"
    else:
        papers_content = "| Title | Authors | Journal | Year |\n|-------|---------|---------|------|\n| No papers found | - | - | - |\n"

    # Combine Subcategories and Papers Content with Markers
    if subcat_content:
        # Update Subcategories section first
        update_section(readme_path, subcat_start, subcat_end, subcat_content)
    else:
        # Remove Subcategories section if it exists
        update_section(readme_path, subcat_start, subcat_end, "")
    
    # Update Papers section
    update_section(readme_path, papers_start, papers_end, papers_content)

# Main function to organize papers
def organize_papers():
    # Get all subdirectories (categories) in the root directory
    categories = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')]
    update_main_readme(categories)
    
    for category in categories:
        # Navigate into the category directory
        os.chdir(category)
        print(f"Processing category: {category}")

        # Get list of subdirectories and PDF files in the current category
        subdirectories = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')]
        pdf_files = glob.glob("*.pdf")
        papers_info = []

        for pdf_file in pdf_files:
            print(f"Processing {pdf_file}")
            title, doi = extract_metadata(pdf_file)
            metadata = None
            if doi:
                metadata = fetch_crossref_metadata(doi)
            if metadata:
                # Extract necessary metadata
                title = metadata.get('title', [title])[0] if metadata.get('title') else title
                authors = ', '.join([author.get('family', '') for author in metadata.get('author', [])])
                journal = metadata.get('container-title', [''])[0]
                journal_url = metadata.get('URL', '')  # URL where the paper is published
                year = metadata.get('published-print', {}).get('date-parts', [[None]])[0][0]
            else:
                authors = journal = journal_url = year = ''
            if not title:
                title = os.path.splitext(os.path.basename(pdf_file))[0]
            # Rename PDF to the paper title
            safe_title = re.sub(r'[\\/:"*?<>|]+', '-', title)  # Replace invalid filename characters
            new_pdf_name = f"{safe_title}.pdf"
            new_pdf_path = os.path.join('.', new_pdf_name)
            if pdf_file != new_pdf_name:
                try:
                    os.rename(pdf_file, new_pdf_name)
                    print(f"Renamed {pdf_file} to {new_pdf_name}")
                except Exception as e:
                    print(f"Error renaming {pdf_file} to {new_pdf_name}: {e}")
            # Collect paper info
            papers_info.append({
                'title': title,
                'authors': authors,
                'journal': journal,
                'journal_url': journal_url,
                'year': year,
                'pdf_path': new_pdf_name
            })
        
        # Create or update the README.md in the current category
        create_or_update_sub_readme('.', subdirectories, papers_info)

        # Move back to the root directory
        os.chdir('..')

# Run the organizer
if __name__ == "__main__":
    organize_papers()
