from openai import OpenAI
import numpy as np
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import re

def get_embedding2(client, text, model="text-embedding-3-small"):
    normalized_text = normalize_text(text)
    return client.embeddings.create(input=[normalized_text], model=model).data[0].embedding

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


def store_chunks(model, env_dict,parsed_files):
    try:
        client = OpenAI(api_key=env_dict['OPENAI_API_KEY'])
        db_host = env_dict['DB_HOST']
        port = env_dict['DB_PORT']
        db_user = env_dict['DB_USER']
        password = env_dict['DB_PASSWORD']
        db_name = env_dict['DB_NAME']
        table_name = env_dict['DB_TABLE_NAME']
        # Connect to the default postgres database to check/create database
        print(f"Starting to embed to {db_name}, table {table_name}")
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=password, host=db_host, port=port)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        i = 0
        for file_chunks in parsed_files:
            for chunk in parsed_files[file_chunks]:
                n = parsed_files[file_chunks][chunk]
                page, position = chunk.split("_")
                text = normalize_text(n['text'])
                if len(text.strip()) > 20:
                    emb = get_embedding2(client, text.strip(), model)
                    embedding_str = np.array(emb).tolist()
                    cursor.execute(f"""
                                    INSERT INTO {table_name} (file, page, position, text_chunk, embedding)
                                    VALUES (%s, %s, %s, %s, %s);
                                """, (file_chunks, int(page), int(position), text, embedding_str))
                    i += 1
                    print(f"\rStored: {i} records", end="", flush=True)
                    if i % 100 == 0:
                        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Exception {e}")

def create_index(env_dict):
    try:
        db_host = env_dict['DB_HOST']
        port = env_dict['DB_PORT']
        db_user = env_dict['DB_USER']
        password = env_dict['DB_PASSWORD']
        db_name = env_dict['DB_NAME']
        table_name = env_dict['DB_TABLE_NAME']
        # Connect to the default postgres database to check/create database
        print(f"Starting to create index on  {db_name}, table {table_name}")
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=password, host=db_host, port=port)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        delete_str = f"DROP INDEX IF EXISTS {db_name}_{table_name}_idx"
        cursor.execute(delete_str)
        query_str = f"CREATE INDEX ON {table_name} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
        cursor.execute(query_str)
        cursor.close()
        conn.close()
        print(f"Index created: {db_name}_{table_name}_idx")
    except Exception as e:
        print(f"Exception {e}")



def setup_database_and_table(model, env_dict):
    db_host = env_dict['DB_HOST']
    port = env_dict['DB_PORT']
    db_user = env_dict['DB_USER']
    password = env_dict['DB_PASSWORD']
    db_name = env_dict['DB_NAME']
    table_name = env_dict['DB_TABLE_NAME']
    vector_dimension = 1536
    if model == 'text-embedding-3-large':
        vector_dimension = 3072
    # Connect to the default postgres database to check/create database
    conn = psycopg2.connect(dbname='postgres', user=db_user, password=password, host=db_host, port=port)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Check if database exists
    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
    exists = cursor.fetchone()
    if not exists:
        cursor.execute(f'CREATE DATABASE {db_name}')
        print(f'Database {db_name} created.')
    else:
        print(f'Database {db_name} already exists.')

    cursor.close()
    conn.close()

    # Connect to the specific database to check/create table
    conn = psycopg2.connect(dbname=db_name, user=db_user, password=password, host=db_host, port=port)
    cursor = conn.cursor()

    # Ensure the pgvector extension is enabled
    cursor.execute('CREATE EXTENSION IF NOT EXISTS vector;')

    # Check if table exists and create if not
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        file TEXT,
        page INTEGER,
        position INTEGER,
        text_chunk TEXT,
        embedding VECTOR({vector_dimension})
    );
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print(f'Table {table_name} is ready in database {db_name}.')