import asyncio

from django.conf import settings
from openai import OpenAI
from textblob import TextBlob

from chatbackend.logging_config import configure_logger
from optimizers.utils import get_chat_response

logger = configure_logger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def analyze_communication_for_candidate(transcript):
    logger.info(f"----------------------- ANALYZING COMMUNICATION SKILLS -----------------------")
    
    instruction = """
    Analyze the interview transcript for communication skills. Assess the candidate's clarity of expression, listening skills, and ability to articulate complex ideas. Provide specific examples from the transcript where the candidate demonstrated these skills effectively or areas where improvement is needed.
    """
    communication_feedback = await get_chat_response(instruction, transcript)
    # logger.info(f"{communication_feedback}")
    return communication_feedback


async def analyze_technical_knowledge_for_candidate(transcript):
    logger.info(f"----------------------- ANALYZING TECHNICAL KNOWLEDGE -----------------------")
    instruction = """
    Evaluate the technical knowledge of the candidate as shown in the transcript. Focus on their depth of understanding in the relevant technical domain and their problem-solving abilities. Highlight specific instances where technical expertise is evident and suggest areas for improvement.
    """
    technical_feedback = await get_chat_response(instruction, transcript)
    # logger.info(f"{technical_feedback}")
    return technical_feedback


async def analyze_behavioral_competencies_for_candidate(transcript):
    logger.info(f"----------------------- ANALYZING BEHAVIORAL COMPETENCIES -----------------------")

    instruction = """
    Analyze the candidate's behavioral competencies based on the transcript. Assess their teamwork, leadership abilities, and adaptability. Provide feedback on how effectively these competencies are demonstrated during the interview.
    """
    behavioral_feedback = await get_chat_response(instruction, transcript)
    # logger.info(f"{behavioral_feedback}")
    return behavioral_feedback


async def analyze_experience_and_qualifications_for_candidate(transcript):
    logger.info(f"----------------------- ANALYZING EXPERIENCE AND QUALIFICATIONS -----------------------")
    
    instruction = """
    Review the candidate's discussion of their experience and qualifications. Provide feedback on how relevant their experience is to the role they have applied for and how they might better align or present their qualifications.
    """
    experience_feedback = await get_chat_response(instruction, transcript)
    # logger.info(f"{experience_feedback}")
    return experience_feedback


async def analyze_problem_solving_skills_for_candidate(transcript):
    logger.info(f"----------------------- ANALYZING PROBLEM SOLVING SKILLS -----------------------")

    instruction = """
    Evaluate the candidate's problem-solving and critical thinking skills as demonstrated in the interview. Provide feedback on their analytical approach and creativity, with suggestions for further development in these areas.
    """
    problem_solving_feedback = await get_chat_response(instruction, transcript)
    # logger.info(f"{problem_solving_feedback}")
    return problem_solving_feedback


async def analyze_emotional_intelligence_for_candidate(transcript):
    logger.info(f"----------------------- ANALYZING EMOTIONAL INTELLIGENCE -----------------------")
    
    instruction = """
    Assess the candidate's emotional intelligence based on this transcript. Provide advice on how they can improve in areas like empathy, self-awareness, and managing interactions with others.
    """
    emotional_intelligence_feedback = await get_chat_response(instruction, transcript)
    # logger.info(f"{emotional_intelligence_feedback}")
    return emotional_intelligence_feedback


async def analyze_professionalism_for_candidate(transcript):
    logger.info(f"----------------------- ANALYZING PROFESSIONALISM -----------------------")

    instruction = """
    Analyze the candidate's level of professionalism during the interview. Give tips on how they can present themselves more professionally and prepared in future interviews.
    """
    professionalism_feedback = await get_chat_response(instruction, transcript)
    # logger.info(f"{professionalism_feedback}")
    return professionalism_feedback


async def analyze_sentiment_for_candidate(transcript):
    logger.info(f"----------------------- ANALYZING SENTIMENT -----------------------")

    analysis = TextBlob(transcript)
    polarity = analysis.sentiment.polarity  # Polarity score
    subjectivity = analysis.sentiment.subjectivity  # Subjectivity score

    sentiment_feedback = "Your interview responses seem "
    sentiment_feedback += "mostly positive" if polarity > 0.1 else "mostly negative" if polarity < -0.1 else "quite neutral"
    sentiment_feedback += ". "
    sentiment_feedback += "They also appear to be "
    sentiment_feedback += "subjective" if subjectivity > 0.5 else "objective"
    sentiment_feedback += ". Consider if this tone aligns with how you want to present yourself in professional settings."

    logger.info(f"Sentiment Analysis: Polarity: {polarity}, Subjectivity: {subjectivity}")
    logger.info(f"Sentiment Feedback: {sentiment_feedback}")

    return sentiment_feedback


async def main_analysis(transcript):
    results = {
        "Communication Skills": await analyze_communication_for_candidate(transcript),
        "Technical Knowledge": await analyze_technical_knowledge_for_candidate(transcript),
        "Behavioral Competencies": await analyze_behavioral_competencies_for_candidate(transcript),
        "Experience & Qualification": await analyze_experience_and_qualifications_for_candidate(transcript),
        "Problem Solving Skills": await analyze_problem_solving_skills_for_candidate(transcript),
        "Emotional Intelligence": await analyze_emotional_intelligence_for_candidate(transcript),
        "Professionalism": await analyze_professionalism_for_candidate(transcript),
        "Sentiment Analysis": await analyze_sentiment_for_candidate(transcript),
    }
    return results

# transcript = "Your interview transcript here"
# analysis_results = asyncio.run(main_analysis(transcript))