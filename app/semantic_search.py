import json
import numpy as np
import os
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from google.genai import types
from gemini_client import client

# Get the path to template_embeddings.json relative to this file
CURRENT_DIR = Path(__file__).parent
EMBEDDINGS_PATH = CURRENT_DIR.parent / "template_embeddings.json"

# Load stored embeddings
with open(EMBEDDINGS_PATH, "r") as f:
    TEMPLATE_EMBEDDINGS = json.load(f)

def embed_query(query: str):
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
        config=types.EmbedContentConfig(
            task_type="SEMANTIC_SIMILARITY"
        )
    )
    return np.array(response.embeddings[0].values)

def semantic_search(query: str, top_k=3, threshold=0.75):
    query_embedding = embed_query(query).reshape(1, -1)

    results = []

    for tpl in TEMPLATE_EMBEDDINGS:
        template_embedding = np.array(tpl["embedding"]).reshape(1, -1)

        score = cosine_similarity(query_embedding, template_embedding)[0][0]

        if score >= threshold:
            results.append({
                "template_id": tpl["template_id"],
                "title": tpl["title"],
                "score": round(float(score), 3)
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
