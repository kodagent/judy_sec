import asyncio

from django.conf import settings
from openai import OpenAI
from textblob import TextBlob

from chatbackend.logging_config import configure_logger
from optimizers.utils import get_chat_response

logger = configure_logger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


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


"""
Communication Skills:

Clarity of Expression: Assess how clearly and effectively the candidate communicates their thoughts.
Listening Skills: Evaluate their ability to listen and comprehend questions or comments.
Articulation: Look at their ability to express complex ideas simply and understandably.
Technical Knowledge and Skills (for technical roles):

Depth of Knowledge: Gauge their understanding of specific technical domains relevant to the role.
Problem-Solving Ability: Assess their approach to solving technical problems or case studies.
Behavioral Competencies:

Teamwork: Evaluate their ability to work in a team setting.
Leadership: For roles requiring leadership, assess their ability to lead and motivate others.
Adaptability: Look at their ability to adapt to changing circumstances and challenges.
Experience and Qualifications:

Relevance of Experience: Assess how their past experiences align with the requirements of the role.
Achievements: Evaluate the impact and relevance of their past achievements.
Cultural Fit:

Alignment with Company Values: Assess how well the candidate's values and behaviors align with the company culture.
Motivation: Understand their motivation for applying and how it aligns with the company's direction.
Problem-Solving and Critical Thinking:

Analytical Skills: Evaluate their ability to analyze information and make reasoned decisions.
Creativity: Assess their creativity and ability to come up with innovative solutions.
Emotional Intelligence:

Self-Awareness: Assess their understanding of their own strengths and weaknesses.
Empathy: Evaluate their ability to understand and respond to the feelings of others.
Professionalism and Work Ethic:

Dependability: Look at their reliability and commitment to fulfilling responsibilities.
Professional Manner: Assess their general attitude and professionalism during the interview.
Enthusiasm and Passion:

Interest in the Role: Evaluate their genuine interest and enthusiasm for the position and the field.
Long-Term Aspirations: Understand how this role fits into their long-term career plans.
Learning Agility:

Willingness to Learn: Assess their openness to learning new skills and adapting to new knowledge.
"""