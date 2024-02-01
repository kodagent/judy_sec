import time
from io import BytesIO

from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Flowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from chatbackend.configs.logging_config import configure_logger
from optimizers.samples import improved_resume_dict

logger = configure_logger(__name__)


class HRFlowable(Flowable):
    """
    Horizontal line flowable --- draws a line in a flowable
    """

    def __init__(self, width, thickness=1):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness

    def __repr__(self):
        return f"HRFlowable(width={self.width}, thickness={self.thickness})"

    def draw(self):
        """
        Draw the line
        """
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


# Base style for common properties
base_paragraph_style = ParagraphStyle(
    "BaseParagraph",
    fontName="Helvetica",
    fontSize=11,
    leading=13,
    spaceBefore=6,
    spaceAfter=6,
)

# Styles that extend the base style
name_style = ParagraphStyle(
    "Name",
    parent=base_paragraph_style,
    fontSize=25,
    leading=18,
    spaceAfter=16,
    alignment=TA_LEFT,
    fontName="Helvetica-Bold",
)

contact_details_style = ParagraphStyle(
    "ContactDetails",
    parent=base_paragraph_style,
    spaceAfter=6,
)

linkedin_style = ParagraphStyle(
    "LinkedIn",
    parent=base_paragraph_style,
    textColor=colors.blue,
    underline=True,
)

header_style = ParagraphStyle(
    "Header",
    parent=base_paragraph_style,
    fontSize=14,
    spaceAfter=5,
    fontName="Helvetica-Bold",
)

summary_style = ParagraphStyle(
    "Summary",
    parent=base_paragraph_style,
    spaceBefore=2,
    alignment=TA_JUSTIFY,
)

company_name_style = ParagraphStyle(
    "CompanyName",
    fontName="Helvetica-Bold",
    parent=base_paragraph_style,
)

duration_style = ParagraphStyle(
    "Duration",
    fontName="Helvetica-Bold",
    parent=base_paragraph_style,
    alignment=TA_RIGHT,
)

job_role_style = ParagraphStyle(
    "JobRole",
    parent=base_paragraph_style,
    fontSize=9,
    spaceAfter=0,
)

location_style = ParagraphStyle(
    "Location",
    parent=base_paragraph_style,
    fontSize=9,
    alignment=TA_RIGHT,
)

job_desc_style = ParagraphStyle(
    "JobDesc",
    parent=base_paragraph_style,
    bulletFontName="Helvetica-Bold",
    leftIndent=12,
    bulletIndent=18,
    spaceBefore=3,
    spaceAfter=3,
)

education_style_r = ParagraphStyle(
    "EducationR",
    parent=base_paragraph_style,
    alignment=TA_RIGHT,
)

education_style_l = ParagraphStyle(
    "EducationL",
    parent=base_paragraph_style,
    alignment=TA_LEFT,
)

doc_style_r = ParagraphStyle(
    "DocR",
    parent=base_paragraph_style,
    alignment=TA_RIGHT,
)

doc_style_l = ParagraphStyle(
    "DocL",
    parent=base_paragraph_style,
    alignment=TA_LEFT,
)


# Function to create and style a header with an HRFlowable and Spacer
def add_header_with_line(doc, story, header_text, style):
    story.append(Paragraph(header_text, style))
    story.append(HRFlowable(width=doc.width))
    story.append(Spacer(1, 6))


# Function to create a table for company details and job description
def create_company_table(data, col_widths):
    return Table(
        data,
        colWidths=col_widths,
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        ),
    )


# Function to create a styled Paragraph with an optional hyperlink
def create_styled_paragraph(text, style, hyperlink=None):
    if hyperlink:
        text = f'<link href="{hyperlink}" color="blue">{text}</link>'
    return Paragraph(text, style)


# Function to create a list of bullet points
def create_bullet_list(items, bullet_style):
    return ListFlowable(
        [ListItem(Paragraph(item, bullet_style)) for item in items],
        bulletType="bullet",
        start="•",
        leftIndent=bullet_style.leftIndent,
    )


# Function to add contact information
def add_contact_info(story, contact_dict):
    middle_contact_details = (
        f"{contact_dict['email']} | {contact_dict['phone']} | {contact_dict['address']}"
    )

    # Append the name with a special style
    story.append(Paragraph(contact_dict["name"], name_style))

    # Append the address
    story.append(Paragraph(middle_contact_details, contact_details_style))

    # Append the LinkedIn URL
    if "linkedIn" in contact_dict:
        # Use Paragraph to allow link styling
        linkedin = f'<link href="{contact_dict["linkedIn"]}" color="blue">{contact_dict["linkedIn"]}</link>'
        story.append(Paragraph(linkedin, linkedin_style))


# Function to add contact information
def add_summary(story, summary_text):
    # Add a header
    add_header_with_line("SUMMARY", header_style)

    # Append the name with a special style
    story.append(Paragraph(summary_text, summary_style))


# Function to add experiences
def add_experiences(doc, story, exp_dict):
    # Add a header
    add_header_with_line("EXPERIENCES", header_style)

    for exp_value in exp_dict.values():
        company_name = Paragraph(exp_value["company_name"], company_name_style)
        duration = Paragraph(
            exp_value["start_date"] + " – " + exp_value["end_date"], duration_style
        )
        job_role = Paragraph(exp_value["job_role"], job_role_style)
        location = Paragraph(exp_value["location"], location_style)

        # Add a company table
        company_table_data = [[company_name, duration], [job_role, location]]
        story.append(
            create_company_table(company_table_data, [doc.width * 0.5, doc.width * 0.5])
        )

        # Add job descriptions
        story.append(create_bullet_list(exp_value["job_description"], job_desc_style))
        story.append(Spacer(1, 5))


# Function to add education
def add_education(doc, story, edu_list):
    # Add a header
    add_header_with_line("EDUCATION", header_style)

    column_width_large = doc.width * 0.75
    column_width_small = doc.width * 0.25

    for edu in edu_list:
        degree = Paragraph(edu["degree"], education_style_l)
        institution = Paragraph(edu["institution"], education_style_l)
        location = Paragraph(edu["location"], education_style_r)
        end_date = Paragraph(edu["end_date"], education_style_r)

        # Add a education table
        education_table_data = [[institution, end_date], [degree, location]]
        story.append(
            create_company_table(
                education_table_data, [column_width_large, column_width_small]
            )
        )


# Function to add skills
def add_skills(story, skill_list):
    # Add a header
    add_header_with_line("SKILLS", header_style)

    skills_string = ", ".join(skill_list)
    story.append(Paragraph(skills_string, summary_style))


# Function to add certifications
def add_certifications(doc, story, cert_list):
    # Add a header
    add_header_with_line("CERTIFICATIONS", header_style)

    column_width_large = doc.width * 0.75
    column_width_small = doc.width * 0.25

    for cert in cert_list:
        certification_title = Paragraph(
            f"{cert['title']} - {cert['issuing_organization']}", doc_style_l
        )
        date = Paragraph(f"{cert['date_obtained']}", doc_style_r)

        # Add a education table
        certification_table_data = [[certification_title, date]]
        story.append(
            create_company_table(
                certification_table_data, [column_width_large, column_width_small]
            )
        )


# # Function to add projects
# def add_projects(proj_list):
#     for proj in proj_list:
#         story.append(Paragraph(proj["project_title"], header_style))
#         story.append(Paragraph(proj["description"], job_desc_style))


def generate_resume_pdf(improved_resume_dict, filename):
    start_time = time.time()

    # Define the buffer for the PDF
    pdf_buffer = BytesIO()

    # Create a PDF document
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=36)
    story = []

    # Add sections to the document
    add_contact_info(story, improved_resume_dict["contact"])
    story.append(Spacer(1, 8))  # Add some space before the next section
    add_summary(story, improved_resume_dict["summary"])
    story.append(Spacer(1, 8))
    add_experiences(doc, story, improved_resume_dict["experiences"])
    story.append(Spacer(1, 8))
    add_education(doc, story, improved_resume_dict["education"])
    story.append(Spacer(1, 8))
    add_skills(story, improved_resume_dict["skills"])
    story.append(Spacer(1, 8))
    add_certifications(doc, story, improved_resume_dict["certifications"])
    # Optionally add projects if required
    # story.append(Spacer(1, 8))
    # add_projects(story, improved_resume_dict["projects"])

    # Build the PDF
    doc.build(story)

    # Get the PDF data
    pdf_value = pdf_buffer.getvalue()
    pdf_buffer.close()

    total = time.time() - start_time
    logger.info(f"PDF CREATION TIME: {total}")
    return ContentFile(pdf_value, name=filename)


# Constants
LEFT_MARGIN = 65
RIGHT_MARGIN = 40
TOP_MARGIN = 72
BOTTOM_MARGIN = 72
FONT_NAME = "Verdana"
FONT_SIZE = 12

# Register a TrueType font (if needed)
pdfmetrics.registerFont(TTFont(FONT_NAME, "Verdana.ttf"))


def wrap_text(text, width):
    """
    Wraps text to fit within a specified width.
    :param text: The text to be wrapped.
    :param width: The maximum width of a line.
    :return: A list of lines where each line fits within the specified width.
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # Check if adding the next word exceeds the line width
        if pdfmetrics.stringWidth(current_line + word, FONT_NAME, FONT_SIZE) <= width:
            current_line += word + " "
        else:
            # If the line is too long, start a new line
            lines.append(current_line)
            current_line = word + " "

    if current_line:  # Add the last line if it's not empty
        lines.append(current_line)

    return lines


def draw_line(canvas, text, x, y):
    canvas.drawString(x, y, text)


def format_paragraphs(canvas, text_blocks, width, height, y, is_paragraph=True):
    for block in text_blocks:
        if is_paragraph:
            # Treat as a paragraph with potential line wrapping
            wrapped_text = wrap_text(block, width - (LEFT_MARGIN + RIGHT_MARGIN))
        else:
            # Treat as single lines
            wrapped_text = block.split("\n")

        for line in wrapped_text:
            draw_line(canvas, line, LEFT_MARGIN, y)
            y -= 18  # Line spacing
            if y < BOTTOM_MARGIN:
                canvas.showPage()
                y = height - TOP_MARGIN
                canvas.setFont(FONT_NAME, FONT_SIZE)
        y -= 18  # Paragraph spacing
    return y


def generate_formatted_pdf(response_text, filename, doc_type=None):
    start_time = time.time()

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    p.setFont(FONT_NAME, FONT_SIZE)
    y = height - TOP_MARGIN

    if doc_type == "CL":
        if response_text.get("sender_info"):
            # Sender Info
            sender_info = response_text["sender_info"]
            sender_lines = [
                sender_info["name"],
                sender_info["address"],
                sender_info["phone"],
                sender_info["email"],
                sender_info["date"],
            ]
            for line in sender_lines:
                text_width = p.stringWidth(line, "Times-Roman", 12)
                p.drawString(width - text_width - 72, y, line)
                y -= 14

        if response_text.get("recipient_info"):
            # Recipient Info
            recipient_info = response_text["recipient_info"]
            recipient_lines = [
                recipient_info["name"],
                recipient_info["address"],
            ]
            y -= 20  # Add a space before the recipient's info
            for line in recipient_lines:
                p.drawString(72, y, line)
                y -= 14

        # Body text formatting (for dict)
        body_text = response_text.get("body", "")
        paragraphs = body_text.split("\n\n")
        y = format_paragraphs(p, paragraphs, width, height, y, is_paragraph=True)

        # Greeting Text Formatting
        greeting_text = response_text.get("concluding_greetings", "")
        greeting_lines = greeting_text.split("\n\n")
        y = format_paragraphs(p, greeting_lines, width, height, y, is_paragraph=False)
    else:
        # Handle the case where response_text is a string
        paragraphs = response_text.split("\n\n")
        y = format_paragraphs(p, paragraphs, width, height, y, is_paragraph=True)
    p.save()
    buffer.seek(0)

    total = time.time() - start_time
    logger.info(f"PDF CREATION TIME: {total}")
    return ContentFile(buffer.getvalue(), name=filename)


async def run_main():
    from asgiref.sync import sync_to_async

    from optimizers.mg_database import get_job_post_content_async
    from optimizers.models import CoverLetter, JobPost
    from optimizers.samples import (
        improved_cover_letter_dict,
        optimized_cover_letter_dict,
    )
    from optimizers.utils import optimize_doc

    cover_letter_update = sync_to_async(
        CoverLetter.objects.update_or_create, thread_sensitive=True
    )

    # pdf_dict = improved_pdf_dict
    pdf_dict = optimized_cover_letter_dict

    if pdf_dict == improved_cover_letter_dict:
        improved_content = "content"
        pdf = generate_formatted_pdf(pdf_dict, "output.pdf", doc_type="CL")

        candidate_id = "111"

        # Run the synchronous database update_or_create functions concurrently
        cover_letter_instance, cover_letter_created = await cover_letter_update(
            cover_letter_id=candidate_id,
            defaults={
                "general_improved_content": improved_content,
                "general_improved_pdf": pdf,
            },
        )
    elif pdf_dict == optimized_cover_letter_dict:
        pdf = generate_formatted_pdf(
            pdf_dict, filename="Optimized Cover Letter", doc_type="CL"
        )
