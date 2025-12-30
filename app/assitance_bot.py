from google import genai
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

CURRENT_DIR = Path(__file__).parent.resolve()  # Get absolute path
REGISTRY_PATH = (CURRENT_DIR.parent / "config" / "fields_registry.json").resolve()

SYSTEM_PROMPT = """
You are an assistant helping users fill RTI application forms.
.
Your responsibilities:
- Explain what a form field means
- Guide users on where to find the information
- Suggest legally acceptable generic wording if exact details are unknown

Strict rules:
- Do NOT invent names, addresses, dates, or personal details
- Do NOT answer general RTI law questions
- Do NOT auto-fill or submit forms
- If unsure, clearly say you are unsure
"""

def load_field_registry():
    with open(REGISTRY_PATH, "r") as f:
        return json.load(f)

FIELD_REGISTRY = load_field_registry()

def assist_user(
    metadata: dict,
    field_name: str,
    user_question: str,
    current_form_state: dict
):
    field_info = FIELD_REGISTRY.get(field_name, {})

    user_prompt = f"""
Template Title: {metadata.get("title")}
Category: {metadata.get("category")}
Departments: {", ".join(metadata.get("departments", []))}
Description: {metadata.get("description", "")}

Field Name: {field_name}
Field Label: {field_info.get("label", "")}
Field Help: {field_info.get("description", "")}

Current Field Value: {current_form_state.get(field_name, "")}

User Question: {user_question}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_prompt,
            config={
                "system_instruction": SYSTEM_PROMPT
            }
        )
        return response.text.strip()
    
    except Exception as e:
        return f"❌ Error generating response: {str(e)}"