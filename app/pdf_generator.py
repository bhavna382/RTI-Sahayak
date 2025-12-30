"""
PDF Generation Module for RTI Sahayak
Generates editable RTI application forms using Jinja templates and ReportLab
"""

import io
from jinja2 import Template
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from pathlib import Path


def load_template_file(template_folder_path):
    """Load the Jinja template file."""
    template_path = Path(template_folder_path) / "template.jinja"
    with open(template_path, "r", encoding="utf-8") as f:
        return Template(f.read())


def render_template_text(template, form_data):
    """Render the Jinja template with form data."""
    rendered = template.render(**form_data)
    # Replace rupee symbol with 'Rs.' to avoid font rendering issues
    rendered = rendered.replace('₹', 'Rs. ').replace('₨', 'Rs. ')
    return rendered


def generate_pdf_bytes(rendered_text, title="RTI Application"):
    """
    Generate PDF from rendered text using ReportLab.
    Returns PDF as bytes.
    """
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
        title=title
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles with improved line spacing
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,  # Line height - space between lines
        alignment=TA_LEFT,
        spaceAfter=4  # Small space after each line to match preview
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16, 
        spaceAfter=8,  # Space after headings
        spaceBefore=12,  # Space before headings
        alignment=TA_LEFT
    )
    
    # Build story (content)
    story = []
    
    # Split text into paragraphs
    lines = rendered_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 0.12*inch))  # Empty line spacing to match preview
            continue
        
        # Escape XML special characters for ReportLab
        line = line.replace('&', '&amp;')
        line = line.replace('<', '&lt;')
        line = line.replace('>', '&gt;')
        
        # Check if line is a heading (starts with ** or is all caps with colon)
        if line.startswith('**') and line.endswith('**'):
            # Bold heading
            heading_text = line.replace('**', '').strip()
            para = Paragraph(f"<b>{heading_text}</b>", heading_style)
        elif line.isupper() and ':' in line:
            # All caps heading
            para = Paragraph(f"<b>{line}</b>", heading_style)
        elif line.startswith('[') and ']' in line[:5]:
            # Numbered point
            para = Paragraph(line, normal_style)
        else:
            # Normal paragraph
            para = Paragraph(line, normal_style)
        
        story.append(para)
    
    # Build PDF
    doc.build(story)
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def create_rti_pdf(template_folder_path, form_data, title="RTI Application"):
    """
    Main function to create RTI PDF from template and form data.
    
    Args:
        template_folder_path: Path to the template folder containing template.jinja
        form_data: Dictionary with form field values
        title: PDF document title
    
    Returns:
        tuple: (rendered_text, pdf_bytes)
    """
    # Load and render template
    template = load_template_file(template_folder_path)
    rendered_text = render_template_text(template, form_data)
    
    # Generate PDF
    pdf_bytes = generate_pdf_bytes(rendered_text, title)
    
    return rendered_text, pdf_bytes
