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
def add_header_with_line(doc=None, story=None, header_text=None, style=header_style):
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
    name_text = contact_dict.get("name", "")
    email_text = contact_dict.get("email", "")
    phone_text = contact_dict.get("phone", "")
    address_text = contact_dict.get("address", "")
    linkedIn_url = contact_dict.get("linkedIn", "")

    middle_contact_details = f"{email_text} | {phone_text} | {address_text}"

    # Append the name with a special style
    story.append(Paragraph(name_text, name_style))

    # Append the address
    story.append(Paragraph(middle_contact_details, contact_details_style))

    # Append the LinkedIn URL
    if "linkedIn" in contact_dict:
        # Use Paragraph to allow link styling
        linkedin = f'<link href="{linkedIn_url}" color="blue">{linkedIn_url}</link>'
        story.append(Paragraph(linkedin, linkedin_style))


# Function to add contact information
def add_summary(doc=None, story=None, summary_text=None):
    add_header_with_line(doc=doc, story=story, header_text="SUMMARY")

    # Append the name with a special style
    story.append(Paragraph(summary_text, summary_style))


# Function to add experiences
def add_experiences(doc, story, exp_dict):
    add_header_with_line(doc=doc, story=story, header_text="EXPERIENCES")

    for exp_value in exp_dict.values():
        company_name_text = exp_value.get("company_name", "")
        start_date_text = exp_value.get("start_date", "")
        end_date_text = exp_value.get("end_date", "")
        job_role_text = exp_value.get("job_role", "")
        location_text = exp_value.get("location", "")
        job_description_list = exp_value.get("job_description", "")

        company_name = Paragraph(company_name_text, company_name_style)
        duration = Paragraph(start_date_text + " – " + end_date_text, duration_style)
        job_role = Paragraph(job_role_text, job_role_style)
        location = Paragraph(location_text, location_style)

        # Add a company table
        company_table_data = [[company_name, duration], [job_role, location]]
        story.append(
            create_company_table(company_table_data, [doc.width * 0.5, doc.width * 0.5])
        )

        # Add job descriptions
        story.append(create_bullet_list(job_description_list, job_desc_style))
        story.append(Spacer(1, 5))


# Function to add education
def add_education(doc, story, edu_list):
    add_header_with_line(doc=doc, story=story, header_text="EDUCATION")

    column_width_large = doc.width * 0.75
    column_width_small = doc.width * 0.25

    for edu in edu_list:
        degree_text = edu.get("degree", "")
        institution_text = edu.get("institution", "")
        location_text = edu.get("location", "")
        end_date_text = edu.get("end_date", "")

        degree = Paragraph(degree_text, education_style_l)
        institution = Paragraph(institution_text, education_style_l)
        location = Paragraph(location_text, education_style_r)
        end_date = Paragraph(end_date_text, education_style_r)

        # Add a education table
        education_table_data = [[institution, end_date], [degree, location]]
        story.append(
            create_company_table(
                education_table_data, [column_width_large, column_width_small]
            )
        )


# Function to add skills
def add_skills(doc=None, story=None, skill_list=None):
    add_header_with_line(doc=doc, story=story, header_text="SKILLS")

    skills_string = ", ".join(skill_list)
    story.append(Paragraph(skills_string, summary_style))


# Function to add certifications
def add_certifications(doc=None, story=None, cert_list=None):
    add_header_with_line(doc=doc, story=story, header_text="CERTIFICATIONS")

    column_width_large = doc.width * 0.75
    column_width_small = doc.width * 0.25

    for cert in cert_list:
        title_text = cert.get("title", "")
        issuing_organization_text = cert.get("issuing_organization", "")
        date_obtained_text = cert.get("date_obtained", "")

        certification_title = Paragraph(
            f"{title_text} - {issuing_organization_text}", doc_style_l
        )
        date = Paragraph(f"{date_obtained_text}", doc_style_r)

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
    add_contact_info(story, improved_resume_dict.get("contact", ""))
    story.append(Spacer(1, 8))  # Add some space before the next section
    add_summary(
        doc=doc,
        story=story,
        summary_text=improved_resume_dict.get("summary", ""),
    )
    story.append(Spacer(1, 8))
    add_experiences(doc, story, improved_resume_dict.get("experiences", ""))
    story.append(Spacer(1, 8))
    add_education(doc, story, improved_resume_dict.get("education", ""))
    story.append(Spacer(1, 8))
    add_skills(doc, story, improved_resume_dict.get("skills", ""))
    story.append(Spacer(1, 8))
    add_certifications(doc, story, improved_resume_dict.get("certifications", ""))
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


improved_resume_dict = {
    "contact": {
        "name": "SARAH JOHNSON",
        "address": "Seattle, Washington",
        "phone": "+1-555-123-4567",
        "email": "sjohnsonnurse@example.com",
        "linkedIn": "https://www.linkedin.com/in/sarah-johnson-rn",
    },
    "summary": "Highly experienced and strategic Registered Nurse with over 10 years of clinical experience, including 5+ years in leadership roles focused on inpatient care. Proven track record in enhancing patient care, streamlining department operations, and leading healthcare teams towards excellence. Eager to contribute to AMCE's mission by bringing a culture of clinical excellence and patient-centered care to a diverse patient population.",
    "experiences": {
        "experience_1": {
            "company_name": "Seattle General Hospital",
            "job_role": "Registered Nurse",
            "start_date": "June 2019",
            "end_date": "Present",
            "location": "Seattle, Washington",
            "job_description": [
                "Oversee patient care delivery in a high-traffic emergency department, developing and executing strategies to reduce wait times and enhance service quality.",
                "Spearhead a comprehensive review and overhaul of patient triage protocol, resulting in a 30% leap in departmental efficiency and patient throughput.",
                "Pioneer patient education initiatives to tackle chronic disease management, yielding a significant improvement in patient compliance and outcomes.",
            ],
        },
        "experience_2": {
            "job_title": "Staff Nurse",
            "start_date": "January 2017",
            "end_date": "June 2019",
            "job_description": "Managed and coordinated end-to-end patient care for various medical cases within a 30-bed inpatient unit, consistently scoring high on patient satisfaction metrics.",
        },
        "experience_3": {
            "job_title": "Community Health Nurse",
            "start_date": "July 2015",
            "end_date": "December 2016",
            "job_description": "Executed primary care services and health education for underserved communities, with an emphasis on preventative care and wellness.",
        },
    },
    "education": [
        {
            "institution": "University of Washington",
            "degree": "Master of Science in Nursing (MSN)",
            "end_date": "June 2015",
            "location": "Seattle, Washington",
            "details": "Focused on Healthcare Leadership and Management",
        }
    ],
    "skills": [
        "Clinical Management",
        "Team Leadership",
        "Strategic Planning",
        "Patient Education",
        "Quality Assurance",
        "Healthcare Regulation Compliance",
        "Interdisciplinary Collaboration",
        "Health Informatics",
        "Patient Advocacy",
        "Mentorship Programs",
    ],
    "certifications": [
        {
            "title": "Certified Emergency Nurse (CEN)",
            "issuing_organization": "Institute of Michigan",
            "date_obtained": "August 2016",
            "validity_period": None,
        },
        {
            "title": "Trauma Nursing Core Course (TNCC)",
            "issuing_organization": "Institute of Michigan",
            "date_obtained": "March 2018",
            "validity_period": "4 years",
        },
        {
            "title": "Pediatric Advanced Life Support (PALS)",
            "issuing_organization": "Institute of Michigan",
            "date_obtained": "May 2017",
            "validity_period": "2 years",
        },
        {
            "title": "Registered Nurse (RN) License, State of Washington",
            "issuing_organization": "Institute of Michigan",
            "date_obtained": "June 2015",
            "validity_period": None,
        },
    ],
    "references": [
        {
            "referee_name": "Available upon request.",
            "relationship": None,
            "contact_information": None,
        }
    ],
}
# generate_resume_pdf(improved_resume_dict, filename="resume.pdf")

# Constants
LEFT_MARGIN = 65
RIGHT_MARGIN = 40
TOP_MARGIN = 72
BOTTOM_MARGIN = 72
FONT_NAME = "Helvetica"
FONT_SIZE = 12


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


async def generate_formatted_pdf(response_text, filename, doc_type=None):
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
