
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
import random

CURRENT_DIR = Path(__file__).parent.resolve()  # Get absolute path
TEMPLATES_DIR = (CURRENT_DIR.parent / "templates").resolve()
REGISTRY_PATH = (CURRENT_DIR.parent / "config" / "fields_registry.json").resolve()
EMBEDDINGS_PATH = (CURRENT_DIR.parent / "template_embeddings.json").resolve()

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
    # Custom CSS to match the second image (narrower, centered)
    st.markdown("""
    <style>
    .header-box {
        background: transparent;
        padding: 35px 40px;
        text-align: center;
        color: white;
        margin: -100px -100px 40px -100px;
        padding-left: calc(40px + 100px);
        padding-right: calc(40px + 100px);
        border-radius: 15px;
    }
    .header-box h1 {
        font-size: 3.2em;
        margin: 0 0 15px 0;
        font-weight: 800;
        letter-spacing: 1px;
    }
    .header-box p {
        font-size: 1.1em;
        margin: 0;
        opacity: 0.95;
        font-weight: 400;
        letter-spacing: 0.5px;
    }
    .search-container {
        max-width: 800px;
        margin: 30px auto 50px auto;
        display: flex;
        gap: 12px;
        align-items: center;
    }
    .search-input {
        flex: 1;
    }
    .about-section {
        background: rgba(30, 30, 50, 0.3);
        padding: 35px 30px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        margin: 50px auto 40px auto;
        max-width: 800px;
        text-align: center;
    }
    .about-section h3 {
        color: #fff;
        margin: 0 0 12px 0;
        font-size: 1.2em;
        font-weight: 600;
    }
    .about-section p {
        color: rgba(255,255,255,0.75);
        line-height: 1.6;
        margin: 0;
        font-size: 0.95em;
    }
    .footer {
        text-align: center;
        padding: 20px;
        color: rgba(255,255,255,0.6);
        margin-top: 60px;
        font-size: 0.9em;
        font-weight: 400;
    }
    [data-testid="textInputRootElement"] input {
        font-size: 14px !important;
        padding: 12px 15px !important;
        border-radius: 6px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Centered header box (narrower)
    st.markdown("""
    <div class="header-box">
        <h1>📋 RTI Sahayak</h1>
        <p>Your Assistant for Filing Right to Information Requests</p>
    </div>
    """, unsafe_allow_html=True)

    # Centered Search Section (narrower)
    st.markdown("""<div class="search-container">""", unsafe_allow_html=True)
    col1, col2 = st.columns([3.5, 1])
    with col1:
        query = st.text_input(
            "",
            placeholder="Describe your issue... (e.g., passport delay, pension records)",
            key="search_query",
            label_visibility="collapsed"
        )
    with col2:
        search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
    st.markdown("""</div>""", unsafe_allow_html=True)

    # Store search results in session state
    if "search_results" not in st.session_state:
        st.session_state.search_results = None

    if search_clicked:
        if query:
            st.session_state.search_results = semantic_search(query)
        else:
            st.warning("⚠️ Please describe your issue to search.")
            st.session_state.search_results = None

    # Display results if they exist
    if st.session_state.search_results is not None:
        if not st.session_state.search_results:
            st.warning("❌ We don't have a template for that topic yet.")
            
            # Load available templates for suggestion
            with open(EMBEDDINGS_PATH, "r") as f:
                all_templates = json.load(f)
            
            # Show one random example
            if all_templates:
                example = random.choice(all_templates)
                st.info(f"💡 **Try this instead:** {example['title']}")
                if st.button(f"Use: {example['title']}", key=f"fallback_{example['template_id']}", use_container_width=True):
                    st.session_state.selected_template = example['template_id']
                    st.session_state.search_results = None
                    st.rerun()
        else:
            st.markdown("<h4 style='text-align: center; margin: 30px 0 20px;'>Suggested Templates</h4>", unsafe_allow_html=True)
            for r in st.session_state.search_results:
                if st.button(
                    f"📄 {r['title']} ({int(r['score']*100)}% match)",
                    key=r["template_id"],
                    use_container_width=True
                ):
                    st.session_state.selected_template = r["template_id"]
                    st.session_state.search_results = None
                    st.rerun()

    # About Section
    st.markdown("""
    <div class="about-section">
        <h3>About This Project</h3>
        <p>RTI Sahayak helps you convert simple, natural language queries into complete RTI applications.
           Using AI-driven template matching, guided forms, and built-in validation, it takes you from “I have a problem” to a ready-to-submit RTI — no legal knowledge required.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="footer">
        <p>Built by a student to make government information accessible to all citizens 💙</p>
        <div style="margin-top: 15px; display: flex; justify-content: center; gap: 20px;">
            <a href="https://www.linkedin.com/in/bhavna-s-073986345/" target="_blank" style="text-decoration: none;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="rgba(255,255,255,0.7)" style="transition: fill 0.3s;">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z"/>
                </svg>
            </a>
            <a href="https://github.com/bhavna382" target="_blank" style="text-decoration: none;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="rgba(255,255,255,0.7)" style="transition: fill 0.3s;">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v 3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

