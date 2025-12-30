
import streamlit as st

# Must be the first Streamlit command
st.set_page_config(page_title="RTI Sahayak", page_icon="📄", layout="centered")

from semantic_search import semantic_search
from form_validator import render_field_with_validation, validate_all_fields
from pdf_generator import create_rti_pdf
import json
import os
from datetime import date
from pathlib import Path

CURRENT_DIR = Path(__file__).parent.resolve()  # Get absolute path
TEMPLATES_DIR = (CURRENT_DIR.parent / "templates").resolve()
REGISTRY_PATH = (CURRENT_DIR.parent / "config" / "fields_registry.json").resolve()

# =======================
# UTILITY FUNCTIONS 
# =======================
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_template_folder(template_id):
    """Find the folder name for a given template_id by searching all template folders."""
    for folder in TEMPLATES_DIR.iterdir():
        if folder.is_dir():
            meta_file = folder / "meta.json"
            if meta_file.exists():
                meta = load_json(meta_file)
                if meta.get("template_id") == template_id:
                    return folder.name
    return None


def load_template_meta(template_id):
    # Find the actual folder name for this template_id
    folder_name = find_template_folder(template_id)
    if not folder_name:
        raise FileNotFoundError(f"Template folder not found for template_id: {template_id}")
    
    meta_path = TEMPLATES_DIR / folder_name / "meta.json"
    return load_json(meta_path)


def load_field_registry():
    return load_json(REGISTRY_PATH)


# =======================
# SIDEBAR RTI KNOWLEDGE ASSISTANT
# =======================
def render_sidebar_rti_assistant():
    """Render general RTI knowledge assistant in sidebar."""
    from rti_query_bot import answer_rti_query, get_welcome_message
    
    with st.sidebar:
        st.markdown("### 🤖 RTI Knowledge Assistant")
        st.caption("Ask anything about RTI Act & procedures")
        
        # Initialize general RTI chat
        if "rti_general_chat" not in st.session_state:
            st.session_state.rti_general_chat = []
        
        # Show welcome message or chat history
        if len(st.session_state.rti_general_chat) == 0:
            st.markdown(get_welcome_message())
        else:
            with st.container(height=350):
                for msg in st.session_state.rti_general_chat:
                    if msg["role"] == "user":
                        with st.chat_message("user"):
                            st.markdown(msg["content"])
                    else:
                        with st.chat_message("assistant"):
                            st.markdown(msg["content"])
        
        st.divider()
        
        # Question input
        user_question = st.text_area(
            "Your question:",
            key="rti_general_question",
            placeholder="e.g., What is the RTI Act? How do I file an appeal?",
            height=100
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📤 Ask", key="rti_general_ask", use_container_width=True):
                if user_question.strip():
                    # Add user message
                    st.session_state.rti_general_chat.append({
                        "role": "user",
                        "content": user_question
                    })
                    
                    # Get bot response
                    with st.spinner("🤔 Thinking..."):
                        try:
                            reply = answer_rti_query(
                                question=user_question,
                                chat_history=st.session_state.rti_general_chat[:-1]  # Exclude current question
                            )
                        except Exception as e:
                            reply = f"Sorry, error: {str(e)}"
                    
                    # Add bot response
                    st.session_state.rti_general_chat.append({
                        "role": "bot",
                        "content": reply
                    })
                    st.rerun()
        
        with col2:
            if st.button("🗑️ Clear", key="rti_general_clear", use_container_width=True):
                st.session_state.rti_general_chat = []
                st.rerun()
        
        st.divider()
        st.caption("ℹ️ **This is for general RTI knowledge.**")
        st.caption("💡 **Use the ⓘ buttons next to fields for form-specific help.**")


# =======================
# SEARCH PAGE
# =======================
def render_search_page():
    st.title("RTI Sahayak")
    st.caption("Find the right RTI template for your issue")

    query = st.text_input(
        "Describe your issue",
        placeholder="e.g. Passport police verification delay",
        key="search_query"
    )

    search_clicked = st.button("🔍 Search ", type="primary")

    # Store search results in session state to persist them
    if "search_results" not in st.session_state:
        st.session_state.search_results = None

    if search_clicked:
        if query:
            st.session_state.search_results = semantic_search(query)
        else:
            st.warning("⚠️ Please enter a description of your issue to search.")
            st.session_state.search_results = None

    # Display results if they exist
    if st.session_state.search_results is not None:
        if not st.session_state.search_results:
            st.warning("No matching template found.")
        else:
            st.subheader("Suggested Templates")
            for r in st.session_state.search_results:
                if st.button(
                    f"{r['title']} (score: {round(r['score'], 2)})",
                    key=r["template_id"]
                ):
                    st.session_state.selected_template = r["template_id"]
                    st.session_state.search_results = None  # Clear results
                    st.rerun()

# =======================
# FORM PAGE
# =======================
def render_form_page():
    template_id = st.session_state.selected_template

    meta = load_template_meta(template_id)
    registry = load_field_registry()
    
    # Render sidebar RTI knowledge assistant (no form context needed)
    render_sidebar_rti_assistant()

    st.title(meta["title"])
    st.caption(meta["description"])

    # Initialize session state variables
    if "form_values" not in st.session_state:
        st.session_state.form_values = {}
    
    if "show_errors" not in st.session_state:
        st.session_state.show_errors = False
    
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False
    
    if "form_stage" not in st.session_state:
        # Stages: "filling" -> "editing_document" -> "ready_for_download"
        st.session_state.form_stage = "filling"
    
    if "rendered_text" not in st.session_state:
        st.session_state.rendered_text = ""
    
    if "pdf_bytes" not in st.session_state:
        st.session_state.pdf_bytes = None

    # =======================
    # STAGE 1: FILLING FORM
    # =======================
    if st.session_state.form_stage == "filling":
        # Render fields WITHOUT form wrapper
        req = meta["required_fields"]

        if "user_specific" in req:
            st.subheader("🧍 Applicant Details")
            for field in req["user_specific"]:
                render_field_with_validation(field, registry, st.session_state.form_values, meta, st.session_state.show_errors)

        if "case_specific" in req:
            st.subheader("📂 Case Details")
            for field in req["case_specific"]:
                render_field_with_validation(field, registry, st.session_state.form_values, meta, st.session_state.show_errors)

        if "authority_specific" in req:
            st.subheader("🏛️ Public Authority Details")
            for field in req["authority_specific"]:
                render_field_with_validation(field, registry, st.session_state.form_values, meta, st.session_state.show_errors)

        if "payment" in req:
            st.subheader("💳 RTI Fee Payment")
            for field in req["payment"]:
                render_field_with_validation(field, registry, st.session_state.form_values, meta, st.session_state.show_errors)

        st.divider()
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Submit button for validation
            if st.button("✅ Validate & Continue", type="primary", use_container_width=True):
                # Add auto-generated fields
                for field in meta.get("auto_generated", []):
                    if field == "submission_date":
                        st.session_state.form_values[field] = date.today().strftime("%d-%m-%Y")

                # Validate
                is_valid, error_count = validate_all_fields(st.session_state.form_values, meta, registry)
                
                if not is_valid:
                    st.session_state.show_errors = True
                    st.session_state.form_submitted = True
                    st.error(f"⚠️ Please fix {error_count} error(s) in the form above.")
                    st.rerun()
                else:
                    st.session_state.show_errors = False
                    st.session_state.form_stage = "validated"
                    st.rerun()
        
        with col2:
            if st.button("⬅ Back to search", use_container_width=True):
                reset_form_session()
                st.rerun()

    # =======================
    # STAGE 2: VALIDATED - SHOW GENERATE PDF BUTTON
    # =======================
    elif st.session_state.form_stage == "validated":
        st.success("✅ Form validated successfully!")
        
        st.info("🎉 Your form has been validated. Click the button below to generate the RTI application document.")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("📄 Generate PDF", type="primary", use_container_width=True):
                with st.spinner("Generating document..."):
                    # Get template folder path
                    folder_name = find_template_folder(template_id)
                    template_folder_path = TEMPLATES_DIR / folder_name
                    
                    try:
                        # Generate PDF
                        rendered_text, pdf_bytes = create_rti_pdf(
                            template_folder_path,
                            st.session_state.form_values,
                            title=meta["title"]
                        )
                        
                        st.session_state.rendered_text = rendered_text
                        st.session_state.pdf_bytes = pdf_bytes
                        st.session_state.form_stage = "editing_document"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
        
        with col2:
            if st.button("⬅ Back to edit", use_container_width=True):
                st.session_state.form_stage = "filling"
                st.rerun()

    # =======================
    # STAGE 3: EDITING DOCUMENT
    # =======================
    elif st.session_state.form_stage == "editing_document":
        st.success("✅ RTI Application Document Generated!")
        
        st.subheader("📝 Edit Your RTI Application")
        st.caption("You can edit the text below before downloading the final PDF.")
        
        # Editable text area with the rendered template
        edited_text = st.text_area(
            "RTI Application Content:",
            value=st.session_state.rendered_text,
            height=500,
            key="editable_document"
        )
        
        st.divider()
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # Regenerate PDF with edited text
            if st.button("🔄 Update Preview", use_container_width=True):
                with st.spinner("Updating document..."):
                    try:
                        from pdf_generator import generate_pdf_bytes
                        pdf_bytes = generate_pdf_bytes(edited_text, title=meta["title"])
                        st.session_state.pdf_bytes = pdf_bytes
                        st.session_state.rendered_text = edited_text
                        st.success("Document updated!")
                    except Exception as e:
                        st.error(f"Error updating PDF: {str(e)}")
        
        with col2:
            # Download button
            if st.session_state.pdf_bytes:
                st.download_button(
                    label="📥 Download PDF",
                    data=st.session_state.pdf_bytes,
                    file_name=f"RTI_Application_{date.today().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
        
        with col3:
            if st.button("⬅ Back", use_container_width=True):
                st.session_state.form_stage = "validated"
                st.rerun()


def reset_form_session():
    """Reset all form-related session state."""
    st.session_state.show_errors = False
    st.session_state.form_submitted = False
    st.session_state.form_stage = "filling"
    st.session_state.rendered_text = ""
    st.session_state.pdf_bytes = None
    
    if "form_values" in st.session_state:
        del st.session_state.form_values
    
    # Clear all help states (including RTI general chat)
    for key in list(st.session_state.keys()):
        if key.startswith("help_") or key.startswith("rti_general_"):
            del st.session_state[key]
    
    del st.session_state.selected_template

# =======================
# APP ENTRY POINT (BOTTOM)
# =======================

if "selected_template" not in st.session_state:
    render_search_page()
else:
    render_form_page()



# st.set_page_config(page_title="RTI Sahayak", layout="centered")

# st.title("RTI Sahayak")
# st.caption("Find the right RTI template for your issue")

# query = st.text_input(
#     "Describe your issue",
#     placeholder="e.g. My pension has not been sanctioned after retirement"
# )

# if query:
#     results = semantic_search(query)

#     if not results:
#         st.warning("No matching template found. Try a general RTI.")
#     else:
#         st.subheader("Suggested Templates")
#         for r in results:
#             st.button(
#                 f"{r['title']}  (score: {r['score']})",
#                 key=r["template_id"]
#             )

