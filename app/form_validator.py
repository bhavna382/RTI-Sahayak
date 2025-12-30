""".
Inline Form Validation for RTI Sahayak
Shows validation errors next to each field (like JavaScript forms)
"""

import streamlit as st
import re
from datetime import date
from assitance_bot import assist_user


def render_field_with_validation(field_key, registry, form_state, meta=None, show_errors=False):
    """
    Render a form field with inline validation.
    
    Args:
        field_key: The field identifier
        registry: Field registry configuration
        form_state: Dictionary to store form values
        meta: Template metadata (for label overrides)
        show_errors: Whether to show validation errors (True after form submit)
    
    Returns:
        validation_error: String with error message if validation fails, None otherwise
    """
    config = registry.get(field_key)
    
    if not config:
        st.warning(f"No registry config for field: {field_key}")
        return None
    
    # Check conditional visibility
    conditional = config.get("conditional")
    if conditional:
        show_if_field = conditional.get("show_if")
        equals_value = conditional.get("equals")
        if show_if_field and equals_value:
            # Skip rendering if condition not met
            if form_state.get(show_if_field) != equals_value:
                return None
    
    # Get field label
    if meta and "field_labels" in meta and field_key in meta["field_labels"]:
        label = meta["field_labels"][field_key]
    else:
        label = config.get("label", field_key)
    
    # Note: Removed asterisk for required fields for cleaner UI
    is_required = config.get("required", False)
    
    field_type = config.get("type", "text")
    validation_error = None
    
    # Initialize help state
    help_key = f"help_open_{field_key}"
    if help_key not in st.session_state:
        st.session_state[help_key] = False
    
    # Track last active field - close help when user moves to another field
    if "last_interacted_field" not in st.session_state:
        st.session_state.last_interacted_field = None
    
    # Store previous value to detect interaction
    field_value_key = f"prev_value_{field_key}"
    current_value = form_state.get(field_key, "")
    
    if field_value_key not in st.session_state:
        st.session_state[field_value_key] = current_value
    
    # Detect if this field is being interacted with (value changed or field clicked)
    value_changed = current_value != st.session_state[field_value_key]
    
    if value_changed:
        # User is typing/interacting with this field
        # Close all help sections if moving to a different field
        if st.session_state.last_interacted_field != field_key:
            for key in list(st.session_state.keys()):
                if key.startswith("help_open_"):
                    st.session_state[key] = False
        
        st.session_state.last_interacted_field = field_key
        st.session_state[field_value_key] = current_value
    
    # Create columns for field label and help button
    col_label, col_help = st.columns([0.85, 0.15])
    
    with col_label:
        st.markdown(f"**{label}**")
    
    with col_help:
        if st.button("ⓘ", key=f"help_btn_{field_key}", help="Get help with this field"):
            # Close ALL help sections first
            for key in list(st.session_state.keys()):
                if key.startswith("help_open_"):
                    st.session_state[key] = False
            # Then open only this one
            st.session_state[help_key] = True
            st.rerun()
    
    # Show inline help if open
    if st.session_state[help_key]:
        render_inline_help(field_key, label, meta, form_state)
    
    # Render field based on type (without label since we rendered it above)
    if field_type == "text":
        form_state[field_key] = st.text_input(label, key=field_key, label_visibility="collapsed", value=form_state.get(field_key, ""))
    
    elif field_type == "textarea":
        form_state[field_key] = st.text_area(label, key=field_key, label_visibility="collapsed", value=form_state.get(field_key, ""))
    
    elif field_type == "date":
        date_value = st.date_input(label, key=field_key, label_visibility="collapsed")
        if date_value:
            form_state[field_key] = date_value.strftime("%d-%m-%Y")
        else:
            form_state[field_key] = ""
    
    elif field_type == "select":
        options = config.get("options", [])
        form_state[field_key] = st.selectbox(label, options, key=field_key, label_visibility="collapsed")
    
    elif field_type == "number":
        # Check if it's a pincode field (use text input without +/- buttons)
        if "pin" in field_key.lower():
            form_state[field_key] = st.text_input(
                label,
                placeholder="Enter PIN code",
                key=field_key,
                label_visibility="collapsed",
                value=form_state.get(field_key, "")
            )
        else:
            form_state[field_key] = st.number_input(label, key=field_key, label_visibility="collapsed")
        # else:
        #     form_state[field_key] = st.number_input(label, key=field_key)
    
    # Validate field if errors should be shown
    if show_errors:
        validation_error = validate_single_field(field_key, form_state.get(field_key, ""), config, label)
        
        if validation_error:
            st.error(f"⚠️ {validation_error}")
    
    return validation_error


def render_inline_help(field_key, field_label, meta, form_state):
    """
    Render inline help chat for a specific field.
    """
    help_chat_key = f"help_chat_{field_key}"
    
    if help_chat_key not in st.session_state:
        st.session_state[help_chat_key] = []
    
    with st.expander(f"🤖 Quick Help: {field_label}", expanded=True):
        # Chat history in a compact scrollable container
        if len(st.session_state[help_chat_key]) > 0:
            with st.container(height=250):
                for msg in st.session_state[help_chat_key]:
                    if msg["role"] == "user":
                        with st.chat_message("user"):
                            st.markdown(msg['content'])
                    else:
                        with st.chat_message("assistant"):
                            st.markdown(msg['content'])
        else:
            st.info("👋 How can I help you ?")
        
        # Question input
        question_key = f"question_{field_key}"
        user_question = st.text_input(
            "Your question:",
            key=question_key,
            placeholder="e.g., What should I write here?",
            label_visibility="collapsed"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("📤 Ask", key=f"ask_btn_{field_key}", use_container_width=True):
                if user_question.strip():
                    st.session_state[help_chat_key].append({
                        "role": "user",
                        "content": user_question
                    })
                    
                    with st.spinner("🤔 Thinking..."):
                        try:
                            reply = assist_user(
                                metadata=meta,
                                field_name=field_key,
                                user_question=user_question,
                                current_form_state=form_state
                            )
                        except Exception as e:
                            reply = f"Sorry, error: {str(e)}"
                    
                    st.session_state[help_chat_key].append({
                        "role": "bot",
                        "content": reply
                    })
                    
                    st.rerun()
        
        with col2:
            if st.button("🗑️ Clear", key=f"clear_btn_{field_key}", use_container_width=True):
                st.session_state[help_chat_key] = []
                st.rerun()


def validate_single_field(field_key, value, config, label):
    """
    Validate a single field against its configuration.
    
    Args:
        field_key: Field identifier
        value: Field value to validate
        config: Field configuration from registry
        label: Display label for error messages
    
    Returns:
        Error message string if validation fails, None if valid
    """
    validation = config.get("validation", {})
    
    # Helper to get custom validation message
    def get_message(msg_key, default_msg):
        msg = validation.get("message", "")
        if isinstance(msg, dict):
            return msg.get(msg_key, default_msg)
        elif isinstance(msg, str) and msg:
            return msg
        return default_msg
    
    # Check required fields
    if config.get("required", False):
        if not value or (isinstance(value, str) and not value.strip()):
            return get_message("required", f"{label} is required")
    
    # Skip further validation if field is empty and not required
    if not value or (isinstance(value, str) and not value.strip()):
        return None
    
    # Pattern validation (regex)
    if "pattern" in validation:
        pattern = validation["pattern"]
        if isinstance(value, str) and not re.match(pattern, value):
            return get_message("pattern", f"{label} has invalid format")
    
    # Min length validation
    if "min" in validation:
        min_val = validation["min"]
        if isinstance(value, str) and len(value) < min_val:
            return get_message("min", f"{label} must be at least {min_val} characters")
    
    # Max length validation
    if "max" in validation:
        max_val = validation["max"]
        if isinstance(value, str) and len(value) > max_val:
            return get_message("max", f"{label} must not exceed {max_val} characters")
    
    # Length validation (exact)
    if "length" in validation:
        length = validation["length"]
        if isinstance(value, str) and len(value) != length:
            return get_message("length", f"{label} must be exactly {length} characters")
    
    # Conditional validation
    if "conditional" in validation:
        condition = validation["conditional"]
        depends_on_field = condition.get("depends_on")
        depends_on_value = condition.get("value")
        
        # This would need access to form_state to check conditional dependency
        # Will be handled in the main validation flow
    
    return None


def validate_all_fields(form_state, meta, registry):
    """
    Validate all fields in the form.
    
    Args:
        form_state: Dictionary with all form values
        meta: Template metadata
        registry: Field registry
    
    Returns:
        Tuple of (is_valid: bool, error_count: int)
    """
    error_count = 0
    
    # Get all required fields from meta
    all_required_fields = []
    for category, fields in meta.get("required_fields", {}).items():
        all_required_fields.extend(fields)
    
    for field_key in all_required_fields:
        config = registry.get(field_key, {})
        value = form_state.get(field_key, "")
        
        # Get field label
        if meta and "field_labels" in meta and field_key in meta["field_labels"]:
            label = meta["field_labels"][field_key]
        else:
            label = config.get("label", field_key)
        
        # Validate the field
        error = validate_single_field(field_key, value, config, label)
        if error:
            error_count += 1
    
    is_valid = error_count == 0
    return is_valid, error_count
