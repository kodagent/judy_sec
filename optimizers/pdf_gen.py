import time
from io import BytesIO

from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# Constants
LEFT_MARGIN = 72
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


def generate_formatted_pdf(response_data, filename, doc_type=None):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    p.setFont(FONT_NAME, FONT_SIZE)
    y = height - TOP_MARGIN

    if doc_type == "CL":
        if response_data.get("sender_info"):
            # Sender Info
            sender_info = response_data["sender_info"]
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

        if response_data.get("recipient_info"):
            # Recipient Info
            recipient_info = response_data["recipient_info"]
            recipient_lines = [
                recipient_info["name"],
                recipient_info["address"],
            ]
            y -= 20  # Add a space before the recipient's info
            for line in recipient_lines:
                p.drawString(72, y, line)
                y -= 14

        # Body text formatting (for dict)
        body_text = response_data.get("body", "")
        paragraphs = body_text.split("\n\n")
        y = format_paragraphs(p, paragraphs, width, height, y, is_paragraph=True)

        # Greeting Text Formatting
        greeting_text = response_data.get("concluding_greetings", "")
        greeting_lines = greeting_text.split("\n\n")
        y = format_paragraphs(p, greeting_lines, width, height, y, is_paragraph=False)
    else:
        # Handle the case where response_data is a string
        paragraphs = response_data.split("\n\n")
        y = format_paragraphs(p, paragraphs, width, height, y, is_paragraph=True)
    p.save()
    buffer.seek(0)
    return ContentFile(buffer.getvalue(), name=filename)


pdf_text = """
Dear Hiring Manager,

I am thrilled to apply for the Registered Nurse (RN) - Acute Care position at St. Mary's Health Centre. With my strong background in acute care nursing and a deep commitment to patient-focused care, I am eager to contribute to your team's esteemed reputation for empathetic service and clinical excellence. 
As a dedicated RN with a Bachelor of Science in Nursing from the Toronto School of Health Sciences and over three years of experience in high-pressure acute care settings, I have honed a robust skill set that aligns with the demands of St. Mary's fast-paced environment. My current role at Good Health Hospital in Toronto has equipped me to excel in situations that require swift decision-making, precise assessments, and the execution of intricate treatment plans.

Key achievements in my professional journey include:
1. Effective management of patients with diverse and complex health conditions, ensuring compassionate and proficient treatment.
2. Demonstrating a strong ability to work collaboratively with cross-functional health care teams to enhance patient care plans and outcomes.
3. Advocacy for patient education, ensuring comprehensible discharge processes, which has notably decreased readmission rates.
4. Maintaining diligent documentation practices, thereby enhancing the accuracy and reliability of patient records.

The holistic approach to health care at St. Mary's Health Centre and its emphasis on continuous professional development resonate with me. The prospect of working within an institution that offers a supportive work environment and values staff well-being is highly appealing to me.

Enclosed is my resume for your review. I am eager to discuss how my clinical expertise and personal ethos can align with the noble mission of St. Mary's Health Centre. Please feel free to contact me at your earliest convenience by phone at (647) 555-0198 or via email at emily.johnson@fakemail.com.

Thank you for considering my application. I am confident in my ability to make a meaningful contribution to your distinguished team and am excited about the opportunity to bring my dedication and skills to your institution.

Warm regards,
Emily Johnson 
"""

pdf_dict = {
    # "sender_info": {
    #     "name": "Emily Johnson",
    #     "address": "789 Healing Avenue\nToronto, ON, M4B 1Z6",
    #     "phone": "(647) 555-0198",
    #     "email": "emily.johnson@fakemail.com",
    #     "date": "October 30, 2023",
    # },
    # "recipient_info": {
    #     "name": "Hiring Manager",
    #     "address": "St. Mary's Health Centre\n456 Wellness Road\nToronto, ON, L3T 7P9",
    # },
    "body": "Dear Hiring Manager,\n\nI am thrilled to apply for the Registered Nurse (RN) - Acute Care position at St. Mary's Health Centre. With a solid background in acute care nursing and a commitment to patient-centric care, I look forward to joining your renowned team. \n\nAs an RN with a Bachelor of Science in Nursing from the Toronto School of Health Sciences and over three years of acute care experience, I've developed a skill set well-suited for St. Mary's dynamic environment. My role at Good Health Hospital has sharpened my decision-making, assessment capabilities, and treatment planning.\n\nHere are some key highlights from my career:\n1. Managed a variety of complex health cases with compassion and expertise.\n2. Collaborated with health care teams to improve patient care quality and outcomes.\n3. Advocated for patient education, contributing to reduced readmission rates.\n4. Ensured accurate, reliable documentation of patient records.\n\nI am drawn to St. Mary's holistic approach to health care and its support for professional growth. Working in a facility that prioritizes staff wellness and provides a nurturing work environment aligns with my professional values.\n\nEnclosed is my resume for your consideration. I am keen to discuss how my clinical skills and dedication can support St. Mary's mission. You are welcome to contact me at (647) 555-0198 or emily.johnson@fakemail.com.\n\nThank you for reviewing my application. I am eager to contribute to your reputable team and excited about the chance to apply my skills at your institution.",
    "concluding_greetings": "\n\nWarm regards,\nEmily Johnson",
}


async def run_main():
    from asgiref.sync import sync_to_async

    from optimizers.models import CoverLetter

    cover_letter_update = sync_to_async(
        CoverLetter.objects.update_or_create, thread_sensitive=True
    )

    improved_content = "content"
    pdf = generate_formatted_pdf(pdf_dict, "output.pdf")

    candidate_id = "111"

    # Run the synchronous database update_or_create functions concurrently
    cover_letter_instance, cover_letter_created = await cover_letter_update(
        cover_letter_id=candidate_id,
        defaults={
            "general_improved_content": improved_content,
            "general_improved_pdf": pdf,
        },
    )
