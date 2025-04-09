from arguments import get_env
import json
import psycopg2
import numpy as np
from sklearn.cluster import KMeans
from openai import OpenAI

def conn_db(env_dict):
    db_host = env_dict['DB_HOST']
    port = env_dict['DB_PORT']
    db_user = env_dict['DB_USER']
    password = env_dict['DB_PASSWORD']
    db_name = env_dict['DB_NAME']
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=password,
        host=db_host,
        port=port
    )
    return conn

def ensure_cluster_columns_exist(env_dict):
    conn = conn_db(env_dict)
    table_name = env_dict['DB_TABLE_NAME']
    cursor = conn.cursor()
    cursor.execute(f"""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='{table_name}' AND column_name='cluster_id'
        ) THEN
            ALTER TABLE {table_name} ADD COLUMN cluster_id INTEGER;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='{table_name}' AND column_name='cluster'
        ) THEN
            ALTER TABLE {table_name} ADD COLUMN cluster TEXT;
        END IF;
    END
    $$;
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Connecting to DB and reading of embeddings
def load_embeddings_from_db(env_dict):
    table_name = env_dict['DB_TABLE_NAME']
    conn = conn_db(env_dict)
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, file, page, position, text_chunk, embedding FROM {table_name};")
    rows = cursor.fetchall()
    conn.close()

    ids = []
    files = []
    pages = []
    positions = []
    chunks = []
    embeddings = []

    for row in rows:
        ids.append(row[0])
        files.append(row[1])
        pages.append(row[2])
        positions.append(row[3])
        chunks.append(row[4])
        embedding = [float(x) for x in row[5].strip('[]').split(',')] if isinstance(row[5], str) else list(row[5])
        embeddings.append(embedding)  # assuming that vector is stored as the type vector

    return ids, files, pages, positions, chunks, np.array(embeddings)

# Cluster name via ChatGPT
def generate_cluster_name(client, text_sample):
    prompt = f"What topic does the following text summarize?\n\n\"{text_sample}\""
    response = client.chat.completions.create(

        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Be very brief. Specify the topic title as one to four words."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=40
    )
    return response.choices[0].message.content.strip()

# Clustering of embeddings and name of it
def cluster_from_db(env_dict, client, n_clusters=5):
    table_name = env_dict['DB_TABLE_NAME']
    ids, files, pages, positions, chunks, embeddings = load_embeddings_from_db(env_dict)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(embeddings)

    cluster_texts = {i: [] for i in range(n_clusters)}
    for i, label in enumerate(labels):
        cluster_texts[label].append((chunks[i], embeddings[i]))

    cluster_names = {}
    for label, items in cluster_texts.items():
        center = kmeans.cluster_centers_[label]
        closest_text = min(items, key=lambda x: np.linalg.norm(x[1] - center))[0]
        cluster_names[label] = generate_cluster_name(client, closest_text)
    conn = conn_db(env_dict)
    cursor = conn.cursor()
    for i in range(len(ids)):
        cursor.execute(
            f"UPDATE {table_name} SET cluster_id = %s, cluster = %s WHERE id = %s;",
            (int(labels[i]), cluster_names[labels[i]], ids[i])
        )
    conn.commit()
    cursor.close()
    conn.close()
    clustered = []
    for i in range(len(chunks)):
        clustered.append({
            "file": files[i],
            "page": pages[i],
            "position": positions[i],
            "chunk": chunks[i],
            "cluster": int(labels[i]),
            "cluster_name": cluster_names[labels[i]]
        })

    return clustered

# Example usage
if __name__ == "__main__":
    env_dict = get_env()
    ensure_cluster_columns_exist(env_dict)
    client = OpenAI(api_key=env_dict['OPENAI_API_KEY'])
    clustered_result = cluster_from_db(env_dict, client, n_clusters=25)
    print(json.dumps(clustered_result, ensure_ascii=False, indent=2))