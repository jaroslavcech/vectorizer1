import argparse
import os
import sys

from arguments import parse_args, get_env
from pathlib import Path
from convert_2_pdf import convert_files
from pdf_2_text import files_text_from_directory, token_count, text_price
from store_2_db import store_chunks, setup_database_and_table, create_index

def is_directory_readable(directory):
    if len(os.listdir(directory)) == 0:
        raise argparse.ArgumentTypeError(f"The directory '{directory}' is empty.")
    directory_path = Path(directory)
    if directory_path.exists() and directory_path.is_dir():
        try:
            next(directory_path.iterdir())
            print(f"The directory '{directory_path}' exists and is readable.")
        except PermissionError:
            raise argparse.ArgumentTypeError(f"The directory '{directory_path}' exists but is NOT readable.")
    else:
        raise argparse.ArgumentTypeError(f"The directory '{directory_path}' does not exist.")

def is_directory_writable(directory_path):
    path = Path(directory_path)
    if path.exists() and path.is_dir():
        try:
            test_file = path / '.write_test.tmp'
            with test_file.open('w') as f:
                f.write("test")
            test_file.unlink()
            print(f"The directory '{directory_path}' exists and is writable.")
        except (PermissionError, OSError):
            print(f"The directory '{directory_path}' does not exists or is NOT writable.")
            raise argparse.ArgumentTypeError(f"The directory '{directory_path}' does not exists or is NOT writable.")
    else:
        raise argparse.ArgumentTypeError(f"The directory '{directory_path}' does not exist.")


def list_files_in_directory(root_dir, extensions_string):
    extensions_list = [ext.strip() for ext in extensions_string.split(',')]
    root_path = Path(root_dir)
    return [str(file.relative_to(root_path)) for file in root_path.rglob('*')
            if file.is_file() and file.suffix in extensions_list ]


# Main program
if __name__ == '__main__':
    args = parse_args()
    env_dict = get_env()
    is_directory_readable(args.in_directory)
    infiles = list_files_in_directory(args.in_directory, env_dict["FILE_FORMATS"])
    print(f"Number of infiles: {len(infiles)}")
    is_directory_writable(args.out_directory)
    convert_files(infiles, args.in_directory, args.out_directory)
    parsed = files_text_from_directory(args.out_directory, args.chunk_size, args.overlapping_size, args.embedding_model, args.overlapping_size + 1)
    if args.token_count:
        total_chunks = token_count(parsed)
        price = text_price(args.embedding_model, total_chunks)
        print(f"Total tokens {total_chunks} - price for {args.embedding_model}: {price} USD")
        sys.exit()
    setup_database_and_table(args.embedding_model, env_dict)
    store_chunks(args.embedding_model,env_dict,parsed)
    create_index(env_dict)
    print(f'Embeddings successfully saved')
