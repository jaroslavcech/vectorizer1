# File Embedding and Vectorization Project

## Overview
This project consists of scripts to convert various file formats to PDF, extract text from PDFs, split text into manageable chunks, calculate tokens and prices for embedding models, and store text chunks along with embeddings into a PostgreSQL database.

## Features
- **File Conversion:** Converts `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.odt`, `.txt`, and `.pdf` files to PDF format. This list could be easily extended via record in .env file
- **Text Extraction:** Extracts and splits text from PDF files into chunks suitable for embedding.
- **Token Counting:** Calculates the total number of tokens and the associated cost based on the embedding model.
- **Database Integration:** Stores text chunks and their embeddings into a PostgreSQL database.
- **Vector Embeddings:** Supports multiple embedding models from OpenAI, including `text-embedding-3-small`, `text-embedding-3-large`, and `text-embedding-ada-002`.

## Why PDF?
PDF format is paginated - so we store to the DB page where the similarity is found

## Setup and Requirements

### OpenAI API subscription
You need OpenAI subscription to generate API key 

### pg_vector extension
You need to install `pg_vector` extension to your Postgres DB 

### Libre Office
You need to have Libre office installed - try if it runs in headless mode

### Python Environment
Create a Python virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Required Environment Variables
Create a `.env` file in the project root with the following configuration:

```bash
DB_HOST=<database_host>
DB_PORT=<database_port>
DB_NAME=<database_name>
DB_USER=<database_user>
DB_PASSWORD=<database_password>
DB_TABLE_NAME=<database_table_name>
OPENAI_API_KEY=<your_openai_api_key>
FILE_FORMATS=.pdf,.txt,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.odt
```

## Usage
Run the main script with the following arguments:

```bash
python main.py -i <input_directory> -o <output_directory> -m <embedding_model> -c <chunk_size> -v <overlapping_size>
```

Optional argument to calculate tokens and embedding cost only:

```bash
python main.py -i <input_directory> -o <output_directory> -m <embedding_model> -c <chunk_size> -v <overlapping_size> -t
```

Example:

```bash
python main.py -i input_files -o converted_pdfs -m text-embedding-3-small -c 300 -v 20
```

## Project Structure

```
.
├── arguments.py          # Argument parsing
├── convert_2_pdf.py      # Conversion of various files to PDF
├── main.py               # Main execution script
├── pdf_2_text.py         # PDF text extraction and chunking
├── requirements.txt      # Python dependencies
└── store_2_db.py         # Database operations and embeddings storage
```

## Dependencies
- Python libraries including `openai`, `psycopg2`, `PyMuPDF`, `reportlab`, and others listed in `requirements.txt`.
- LibreOffice bust be installed to convert non-PDF files to PDF format.

## License
This project is provided as-is without warranty. You are free to modify and distribute under your own terms.

