import json
import numpy as np
from google.genai import types
from gemini_client import client
import os
from pathlib import Path

# Load template metadata from all template folders
templates_dir = Path(__file__).parent.parent / "templates"
templates = []

for template_folder in sorted(templates_dir.iterdir()):
    if template_folder.is_dir():
        meta_file = template_folder / "meta.json"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    templates.append(data)
                    print(f"[OK] Loaded: {data.get('template_id', 'unknown')}")
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Error loading {template_folder.name}: {e}")
        else:
            print(f"[SKIP] No meta.json in {template_folder.name}")

template_embeddings = []

for tpl in templates:
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=tpl["description"],
        config=types.EmbedContentConfig(
            task_type="SEMANTIC_SIMILARITY"
        )
    )

    embedding_vector = response.embeddings[0].values

    template_embeddings.append({
        "template_id": tpl["template_id"],
        "title": tpl["title"],
        "embedding": embedding_vector
    })

# Save embeddings to parent directory
output_path = Path(__file__).parent.parent / "template_embeddings.json"
with open(output_path, "w") as f:
    json.dump(template_embeddings, f)

print(f"[OK] Template embeddings generated and saved. Total: {len(template_embeddings)} templates")
