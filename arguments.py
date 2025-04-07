import argparse
import os
from dotenv import load_dotenv

def parse_args():
    parser = argparse.ArgumentParser(description='File embedding/vectorization tool.')

    parser.add_argument('-i', '--in_directory',  type=str, required=True,
                        help='Input directory where the files are located.')

    parser.add_argument('-o', '--out_directory', type=str, required=True,
                        help='Output directory where the converted PDF files are located.')

    parser.add_argument('-m', '--embedding_model', required=True,
                        choices=['text-embedding-3-small', 'text-embedding-3-large','text-embedding-ada-002'],
                        help='Name of the embedding model (e.g., text-embedding-ada-002).')

    parser.add_argument('-c', '--chunk_size',  type=int, required=True,
                        help='Chunk size according to the kind of usage. Semantic search=100 chars (30 chars overlap), document classification=300 chars, RAG=800 chars.')

    parser.add_argument('-v', '--overlapping_size',  type=int, required=True,
                        help='Overlapping size in percents 0 - 40 is recommended value (shorter chunk, larger overlapping).')

    parser.add_argument('-t', '--token_count', action='store_true', required=False,
                        help='It only calculates the total number of tokens and the price.')


    args = parser.parse_args()
    limited_int(args.chunk_size, 50, 8000, 'chunk_size')
    limited_int(args.overlapping_size, 0, 40, 'overlapping_size')
    print('Command line parameters:')
    for key, value in vars(args).items():
        print(f"{key}: {value}")
    return args

def get_env():
    load_dotenv()
    env_dict = {
        "DB_HOST" : os.getenv("DB_HOST"),
        "DB_PORT" : os.getenv("DB_PORT"),
        "DB_NAME" : os.getenv("DB_NAME"),
        "DB_USER" : os.getenv("DB_USER"),
        "DB_PASSWORD" : os.getenv("DB_PASSWORD"),
        "DB_TABLE_NAME": os.getenv("DB_TABLE_NAME"),
        "OPENAI_API_KEY" : os.getenv("OPENAI_API_KEY"),
        "FILE_FORMATS" : os.getenv("FILE_FORMATS")
    }

    truncate_keys = {"OPENAI_API_KEY", "db_password"}
    for key, value in env_dict.items():
        if key in truncate_keys:
            print(f"{key}: {value[:3]}...")
        else:
            print(f"{key}: {value}")

    return env_dict

def limited_int(arg, arg_min, arg_max, variable_name):
    value = int(arg)
    if not (arg_min <= value <= arg_max):
        raise argparse.ArgumentTypeError(f"Value of {variable_name} must be between {arg_min} and {arg_max}.")
    return value