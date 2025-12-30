import json
import numpy as np
from google.genai import types
from gemini_client import client
import os
from pathlib import Path

# Load template metadata from all template folders
templates_dir = Path("../templates")
templates = []

for template_folder in templates_dir.iterdir():
    if template_folder.is_dir():
        meta_file = template_folder / "meta.json"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                templates.append(json.load(f))

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
with open("../template_embeddings.json", "w") as f:
    json.dump(template_embeddings, f)

print("✅ Template embeddings generated and saved to ../template_embeddings.json")
