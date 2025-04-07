import fitz
import tiktoken
import os
from pathlib import Path

prices = {"text-embedding-3-small": 0.02, "text-embedding-3-large": 0.13, "text-embedding-ada-002": 0.1}

def extract_text(pdf):
    result = []
    page_nr = 0
    with fitz.open(pdf) as doc:
        for page in doc:
            result.append(page.get_text())
            page_nr = page_nr + 1
    return result

def token_count(parsed_files):
    print("Counting tokens:", end='', flush=True)
    total = 0
    for file_chunks in parsed_files:
        print(".", end='', flush=True)
        for chunk in parsed_files[file_chunks]:
            n = parsed_files[file_chunks][chunk]
            total += n["length"]
    print("\n")
    return total

def files_text_from_directory(root_dir, chunk_size, overlap, model_name, min_chunk_size=3):
    r_dir = Path(root_dir)
    pdf_files = list(r_dir.glob('*.pdf'))
    result = {}
    for f in pdf_files:
        pages = extract_text(f)
        chunks = split_text_into_chunks(pages, chunk_size, overlap, model_name, min_chunk_size)
        result[os.path.basename(f)] = chunks

    return result

def text_price(model, tokens):
    for key in prices:
        if key == model:
            return round(prices[key] * (tokens / 1000000), 2)
    return 0

def split_text_into_chunks(pages, chunk_size, overlap, model_name, min_chunk_size=3):
    result = {}

    encoding = tiktoken.encoding_for_model(model_name)
    all_tokens = [encoding.encode(page_text) for page_text in pages]

    page_num = 1
    chunk_num = 1
    token_idx = 0

    while page_num <= len(all_tokens):
        tokens = all_tokens[page_num - 1]

        while token_idx < len(tokens):
            end_idx = token_idx + chunk_size

            if end_idx > len(tokens) and page_num < len(all_tokens):
                next_tokens_needed = end_idx - len(tokens)
                tokens += all_tokens[page_num][:next_tokens_needed]
                all_tokens[page_num] = all_tokens[page_num][next_tokens_needed:]

            chunk_tokens = tokens[token_idx:end_idx]
            chunk_text = encoding.decode(chunk_tokens)

            while end_idx < len(tokens) and not chunk_text.endswith((' ', '\n')):
                chunk_tokens.append(tokens[end_idx])
                end_idx += 1
                chunk_text = encoding.decode(chunk_tokens)

            while token_idx > 0 and not encoding.decode([tokens[token_idx]]).startswith((' ', '\n')):
                token_idx -= 1
                chunk_tokens = tokens[token_idx:end_idx]
                chunk_text = encoding.decode(chunk_tokens)

            chunk_key = f"{page_num}_{chunk_num}"
            result[chunk_key] = {
                "text": chunk_text.strip(),
                "length": len(chunk_tokens)
            }

            token_idx = end_idx - overlap
            chunk_num += 1

        page_num += 1
        chunk_num = 1
        token_idx = 0

    return result


