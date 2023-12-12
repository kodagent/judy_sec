import os

import openai
import textstat
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from sklearn.feature_extraction.text import CountVectorizer

SYSTEM_ROLE = "system"
USER_ROLE = "user"

async def get_openai_response(INSTRUCTION, content, functions=None, function_name=None):
    """
        This function is used for getting responses when there is a need for function call otherwise use get_chat_response
    """
    messages = [
        {"role": SYSTEM_ROLE, "content": INSTRUCTION},
        {"role": USER_ROLE, "content": content}
    ]

    if functions:
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=messages,
            functions=functions,
            function_call={'name': function_name},
        )
        return response["choices"][0]["message"]
    else:
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=messages,
        )

        return response["choices"][0]["message"]["content"]


async def get_chat_response(instruction, message):
    chat = ChatOpenAI(temperature=0.7, model_name="gpt-4-0613", openai_api_key=os.getenv("OPENAI_API_KEY"))

    messages = [SystemMessage(content=instruction), HumanMessage(content=message)]

    response = chat(messages).content
    return response


async def match_keywords_func(doc_text, job_description):
    # Configure CountVectorizer to convert text to lowercase
    vectorizer = CountVectorizer(lowercase=True)
    
    # Fit the vectorizer to the job description to extract keywords
    vectorizer.fit([job_description])
    job_keywords = vectorizer.get_feature_names_out()

    # Tokenize the cover letter text to ensure accurate matching
    doc_text_words = set(doc_text.lower().split())
    
    # Find the intersection of job keywords and cover letter words
    matched_keywords = list(doc_text_words.intersection(job_keywords))
    
    # Optionally, calculate a matching score
    matching_score = len(matched_keywords) / len(job_keywords)

    return matched_keywords, matching_score


async def analyze_readability(cover_letter):
    complexity_score = textstat.flesch_kincaid_grade(cover_letter)
    readability_score = textstat.flesch_reading_ease(cover_letter)
    return complexity_score, readability_score


async def get_readability_text(fk_score, fre_score):
    feedback = ""
    if fk_score >= 12:
        feedback += f"- Your resume has a Flesch-Kincaid Grade Level of {fk_score}, indicating a collegiate reading level. Consider simplifying the language for broader accessibility.\n\n"
    else:
        feedback += f"- Your resume has a Flesch-Kincaid Grade Level of {fk_score}, indicating it's suitable for a wide range of readers. Good job!\n\n"
    
    if fre_score <= 60:
        feedback += f"- Your resume has a Flesch Reading Ease score of {fre_score}, which is considered difficult to read. Consider simplifying the language.\n\n"
    else:
        feedback += f"- Your resume has a Flesch Reading Ease score of {fre_score}, which is considered easy to read. Good job!\n\n"
    
    return feedback
