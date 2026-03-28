import json
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from google.genai import types
from gemini_client import client

# Get the path to template_embeddings.json relative to this file
CURRENT_DIR = Path(__file__).parent
EMBEDDINGS_PATH = CURRENT_DIR.parent / "template_embeddings.json"

def _generate_template_embeddings(output_path: Path):
    """Generate embeddings from template metadata when cache file is missing."""
    templates_dir = CURRENT_DIR.parent / "templates"
    template_embeddings = []

    for template_folder in sorted(templates_dir.iterdir()):
        if not template_folder.is_dir():
            continue

        meta_file = template_folder / "meta.json"
        if not meta_file.exists():
            continue

        with open(meta_file, "r", encoding="utf-8") as f:
            tpl = json.load(f)

        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=tpl["description"],
            config=types.EmbedContentConfig(
                task_type="SEMANTIC_SIMILARITY"
            )
        )

        template_embeddings.append({
            "template_id": tpl["template_id"],
            "title": tpl["title"],
            "embedding": response.embeddings[0].values
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template_embeddings, f)


def _load_template_embeddings(path: Path):
    if not path.exists():
        _generate_template_embeddings(path)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


TEMPLATE_EMBEDDINGS = _load_template_embeddings(EMBEDDINGS_PATH)

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
