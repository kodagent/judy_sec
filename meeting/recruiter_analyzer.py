import asyncio

from django.conf import settings
from openai import OpenAI
from textblob import TextBlob

from chatbackend.configs.base_config import openai_client as client
from chatbackend.configs.logging_config import configure_logger
from optimizers.utils import get_chat_response

logger = configure_logger(__name__)


async def analyze_communication_skills(transcript):
    logger.info(f"----------------------- ANALYZING COMMUNICATION SKILLS -----------------------")

    instruction = """
    Provide an objective assessment of the candidate's communication skills from the interview transcript. Evaluate their clarity of expression, listening skills, and ability to articulate complex ideas. Highlight instances demonstrating these skills and any concerns or areas for improvement.
    """
    communication_feedback = await get_chat_response(instruction, transcript)
    
    # logger.info(f"{communication_feedback}")
    return communication_feedback


async def analyze_technical_knowledge(transcript):
    logger.info(f"----------------------- ANALYZING TECHNICAL KNOWLEDGE -----------------------")

    instruction = """
    Assess the candidate's technical knowledge as it relates to the job role. Evaluate their depth of understanding and problem-solving skills. Provide a detailed analysis of their technical proficiency, citing specific examples from the transcript.
    """
    technical_feedback = await get_chat_response(instruction, transcript)
    
    # logger.info(f"{technical_feedback}")
    return technical_feedback


async def analyze_emotional_intelligence(transcript):
    logger.info(f"----------------------- ANALYZING EMOTIONAL INTELLIGENCE -----------------------")

    instruction = """
    Analyze the candidate's emotional intelligence based on their responses during the interview. Assess aspects like self-awareness, empathy, and interpersonal skills. Provide insights on how these qualities may impact their fit for the role and team dynamics.
    """
    emotional_intelligence_feedback = await get_chat_response(instruction, transcript)
    
    # logger.info(f"{emotional_intelligence_feedback}")
    return emotional_intelligence_feedback


async def analyze_sentiment(transcript):
    logger.info(f"----------------------- TONE (POLARITY) -----------------------")

    analysis = TextBlob(transcript)
    polarity = analysis.sentiment.polarity

    # logger.info(f"{polarity}")

    return polarity 


async def analyze_professionalism(transcript):
    logger.info(f"----------------------- ANALYSING PROFESSIONALISM -----------------------")

    instruction = """
    Evaluate the candidate's professionalism and assertiveness based on the interview. Discuss their dependability, professional manner, and how they handle responsibilities. Offer insights into their potential fit within the professional environment of the organization.
    """
    professionalism_feedback = await get_chat_response(instruction, transcript)
    
    # logger.info(f"{professionalism_feedback}")
    return professionalism_feedback


async def analyze_teamwork_and_leadership(transcript):
    logger.info(f"----------------------- ANALYZING TEAMWORK AND LEADERSHIP -----------------------")

    instruction = """
    Assess the candidate's abilities in teamwork and leadership based on the interview transcript. Evaluate their experiences and anecdotes that demonstrate their capacity to work collaboratively in a team and to lead others. Provide a detailed analysis with examples that highlight these competencies.
    """
    teamwork_leadership_feedback = await get_chat_response(instruction, transcript)
    # logger.info(f"{teamwork_leadership_feedback}")
    return teamwork_leadership_feedback


async def analyze_adaptability_and_problem_solving(transcript):
    logger.info(f"----------------------- ANALYZING ADAPTABILITY AND PROBLEM-SOLVING -----------------------")

    instruction = """
    Analyze the candidate's adaptability and problem-solving skills from the interview transcript. Focus on how they approach challenges and changes, and their methodology in solving complex issues. Highlight specific instances where these skills are evident, and provide an assessment of their potential effectiveness in a dynamic work environment.
    """
    adaptability_problem_solving_feedback = await get_chat_response(instruction, transcript)
    # logger.info(f"{adaptability_problem_solving_feedback}")
    return adaptability_problem_solving_feedback


async def analyze_cultural_fit_and_motivation(transcript):
    logger.info(f"----------------------- ANALYZING CULTURAL FIT AND MOTIVATION -----------------------")

    instruction = """
    Evaluate the candidate's alignment with the company's culture and their motivation for applying for the job. Analyze the transcript for cues on their understanding of the company values, their reasons for applying, and how their personal and professional goals align with the organization's direction. Offer insights into their potential integration into the company culture.
    """
    cultural_fit_motivation_feedback = await get_chat_response(instruction, transcript)
    # logger.info(f"{cultural_fit_motivation_feedback}")
    return cultural_fit_motivation_feedback


async def main_analysis(transcript):
    results = {
        "Communication Skills": await analyze_communication_skills(transcript),
        "Technical Knowledge": await analyze_technical_knowledge(transcript),
        "Emotional Intelligence": await analyze_emotional_intelligence(transcript),
        "Professionalism": await analyze_professionalism(transcript),
        "Teamwork & Leadership": await analyze_teamwork_and_leadership(transcript),
        "Adaptibility & Problem Solving": await analyze_adaptability_and_problem_solving(transcript),
        "Cultural Fit & Motivation": await analyze_cultural_fit_and_motivation(transcript),
    }
    return results


# transcript = "Your interview transcript here"
# analysis_results = asyncio.run(main_analysis(transcript))


