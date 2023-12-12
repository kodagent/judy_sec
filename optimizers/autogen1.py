import json
import logging
import os

import autogen
import openai
import textstat
from autogen import (AssistantAgent, GroupChatManager, UserProxyAgent,
                     config_list_from_json)
from django.conf import settings
from dotenv import load_dotenv
from sklearn.feature_extraction.text import CountVectorizer

# optimizer helpers
from helpers.optimizer_utils import (get_cover_letter_instruction,
                                     get_job_post_instruction,
                                     get_resume_instruction,
                                     get_resume_parser_instruction,
                                     job_post_description, llm_config_test,
                                     resume_content)

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config_list = config_list_from_json(env_or_file="optimizers/OAI_CONFIG_LIST.json")
config_list[0]["api_key"] = settings.OPENAI_API_KEY

os.environ['OPENAI_API_KEY'] = settings.OPENAI_API_KEY

SYSTEM_ROLE = "system"
USER_ROLE = "user"

llm_config = {
    "request_timeout": 120,
    "seed": 42,
    "config_list": config_list,
    "temperature": 0,
}

# ===========================================================
# ======================== FUNCTIONS ========================
# ===========================================================
def get_openai_response(INSTRUCTION, content, functions=None, function_name=None):
    messages = [
        {"role": SYSTEM_ROLE, "content": INSTRUCTION},
        {"role": USER_ROLE, "content": content}
    ]

    if functions:
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=messages,
            functions=functions,
            function_name=function_name,
        )
    else:
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=messages,
        )

    return response["choices"][0]["message"]["content"]


def resume_parser(resume_text=None, document_id=None):
    # resume_content = get_doc_data(document_id) 
    resume_section_dict = {}

    sections = [
        "Contact Information",
        "Objective/Summary",
        "Experience",
        "Education",
        "Skills",
        "Certifications",
        "Projects",
        "References"
    ]

    for section in sections:
        instruction = get_resume_parser_instruction(section=section)
        response = get_openai_response(instruction, resume_text)
        resume_section_dict[section] = response
    
    return resume_section_dict


def extract_keywords_text_from_job_description(job_description):
    instruction = f"""Extract the combined texts of the skills, technologies, qualifications sections from the job description. \
        Job description: {job_description}. Do not write any other text except from the keywords seperated with commas ",".
    """
    response = get_openai_response(instruction, job_description)
    
    return response


# def keyword_analysis(resume_text, job_keywords):
#     matching_keywords = []
#     for keyword in job_keywords:
#         if keyword.lower() in resume_text.lower():
#             matching_keywords.append(keyword)
    
#     matching_score = len(matching_keywords) / len(job_keywords)
#     return matching_keywords, matching_score


def keyword_analysis(resume_text, job_description_keywords_section):
    # Configure CountVectorizer to convert text to lowercase
    vectorizer = CountVectorizer(lowercase=True)
    
    # Fit the vectorizer to the job description to extract keywords
    vectorizer.fit([job_description_keywords_section])
    job_keywords = vectorizer.get_feature_names_out()

    # Tokenize the cover letter text to ensure accurate matching
    resume_text_words = set(resume_text.lower().split())
    
    # Find the intersection of job keywords and cover letter words
    matched_keywords = resume_text_words.intersection(job_keywords)
    
    # Optionally, calculate a matching score
    matching_score = len(matched_keywords) / len(job_keywords)

    return matched_keywords, matching_score


def readability_analysis(resume_text):
    fk_score = textstat.flesch_kincaid_grade(resume_text)
    fre_score = textstat.flesch_reading_ease(resume_text)
    return fk_score, fre_score


def get_readability_text(fk_score, fre_score):
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


def analyze_impact(text):
    instruction = "Identify and evaluate quantifiable achievements in the following text."
    response = get_openai_response(instruction, text)
    return response


def score_impact(impact_dict):
    # Define maximum points for each metric
    max_points = {
        'patient_outcomes': 10,
        'process_improvements': 10,
        'cost_management': 10,
        'team_management': 10,
        'certifications': 10,
        'patient_satisfaction': 10
    }
    
    # Assume achievements is a dict with the same keys as max_points, 
    # and values representing the achieved level as a percentage (0 to 1)
    score = sum(impact_dict[metric] * max_points[metric] for metric in impact_dict)
    return score


def score_job_role(role_description):
    instruction = f"""
    Evaluate the following job role description based on these metrics (score out of 10):
    1. Patient Outcomes
    2. Process Improvements
    3. Cost Management
    4. Team Management
    5. Certifications
    6. Patient Satisfaction
    
    {role_description}
    """
    response = get_openai_response(instruction, role_description)
    # Assume response contains scores for each metric
    return response


def get_section_feedback(section_name, section_content):
    instruction = f"""
    You are a knowledgeable career advisor. Analyze the following content from the '{section_name}' section of a resume and provide constructive feedback:

    {section_content}
    """
    feedback = get_openai_response(instruction, section_content)
    return feedback


def provide_complete_feedback(matching_keywords, complexity_score, readability_score, section_feedback):
    feedback = "Feedback on your resume:\n\n"

    # Keyword Feedback
    feedback += "Keyword Matching:\n"
    feedback += f"- Matched Keywords: {', '.join(matching_keywords)}\n"

    # Readability Feedback
    feedback += "Readability:\n"
    feedback += get_readability_text(complexity_score, readability_score)
    
    # Section-wise Feedback
    feedback += "Section-wise Feedback:\n"
    for section, section_fb in section_feedback.items():
        feedback += f"- {section}: {section_fb}\n"

    return feedback


def optimize_resume(resume_content, job_description, resume_feedback):
    instruction = f"""
    Please provide an optimized version of the resume using the feedback provided.
    Do not change the email details. 
    Do not change/remove work experience details unless it is absolutely necessary.
    Do not change the number of work experience years in the summary.
    """

    content = f"""
    Given the resume feedback, optimize the resume:

    ORIGINAL CONTENT:
    {resume_content}

    JOB DESCRIPTION:
    {job_description}

    RESUME FEEDBACK:
    {resume_feedback}
    """
    optimized_content = get_openai_response(instruction, content)
    return optimized_content

# ===========================================================
# ======================== FUNCTIONS ========================
# ===========================================================
def perform_general_analysis(query):
    llm_config_test["config_list"] = config_list
    # llm_config_general_optimizer["config_list"] = config_list

    analyzer = autogen.AssistantAgent(
        name="analyzer",
        system_message=f"analyzes the resume.",
        llm_config=llm_config_test
    )

    optimizer = autogen.AssistantAgent(
        name="optimizer",
        system_message=f"optimizers the resume.",
        llm_config=llm_config_test
    )

    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="ALWAYS",
        is_termination_msg=lambda x: (x.get("content") or "").rstrip().endswith("TERMINATE"),
        # is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        max_consecutive_auto_reply=10,
        code_execution_config={
            "last_n_messagaes": 2,
            "work_dir": "groupchat",
            "use_docker": False,  # set to True or image name like "python:3" to use docker
        },
    )

    # register the functions
    user_proxy.register_function(
        function_map={
            "extract_keywords_text_from_job_description": extract_keywords_text_from_job_description,
            "keyword_analysis": keyword_analysis,
            "readability_analysis": readability_analysis,
            "get_readability_text": get_readability_text,
            # "score_job_role": score_job_role,
            # "score_impact": score_impact,
            "resume_parser": resume_parser,
            "get_section_feedback": get_section_feedback,
            "provide_complete_feedback": provide_complete_feedback,
        }
    )
    
    groupchat = autogen.GroupChat(agents=[user_proxy, analyzer, optimizer], messages=[], max_round=12)
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config_test)
    
    added_query = f"{query}: {resume_content}"
    user_proxy.initiate_chat(manager, message=added_query)

    # # set the receiver to be analyzer, and get the summary of the analysis
    # user_proxy.stop_reply_at_receive(analyzer)
    # user_proxy.send(
    #     "Give me the analysis feedback"
    # )

    return user_proxy.last_message()["content"]


# def perform_section_analysis(query):
#     llm_config_general_analyzer["config_list"] = config_list
    
#     analyzer = autogen.AssistantAgent(
#         name="analyzer",
#         system_message=f"analyzes the resume given and gives feedback.",
#         llm_config=llm_config_general_analyzer
#     )

#     user_proxy = autogen.UserProxyAgent(
#         name="user_proxy",
#         human_input_mode="NEVER",
#         is_termination_msg=lambda x: (x.get("content") or "").rstrip().endswith("TERMINATE"),
#         # is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
#         code_execution_config={
#             "last_n_messagaes": 2,
#             "work_dir": "coding",
#             "use_docker": False,  # set to True or image name like "python:3" to use docker
#         },
#     )

#     # register the functions
#     user_proxy.register_function(
#         function_map={
#             "extract_keywords_text_from_job_description": extract_keywords_text_from_job_description,
#             "keyword_analysis": keyword_analysis,
#             "readability_analysis": readability_analysis,
#             "get_readability_text": get_readability_text,
#             # "score_job_role": score_job_role,
#             # "score_impact": score_impact,
#             "resume_parser": resume_parser,
#             "get_section_feedback": get_section_feedback,
#             "provide_complete_feedback": provide_complete_feedback,
#         }
#     )
    
#     added_query = f"{query}: {resume_content}"
#     user_proxy.initiate_chat(analyzer, message=added_query)

#     # # set the receiver to be analyzer, and get the summary of the analysis
#     # user_proxy.stop_reply_at_receive(analyzer)
#     # user_proxy.send(
#     #     "Give me the analysis feedback"
#     # )

#     return user_proxy.last_message()["content"]


# # create a UserProxyAgent instance named "user_proxy"
# user_proxy = autogen.UserProxyAgent(
#     name="user_proxy",
#     system_message="An experienced Recruiter, that uses all the tools at her disposal to improve and optimize a resume to for a job role description",
#     human_input_mode="ALWAYS",
#     max_consecutive_auto_reply=10,
#     is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
#     code_execution_config={
#         # "last_n_messagaes": 2,
#         "work_dir": "coding",
#         "use_docker": False,  # set to True or image name like "python:3" to use docker
#     },
# )

# # create an AssistantAgent named "assistant"
# assistant = autogen.AssistantAgent(
#     name="assistant",
#     system_message="",
#     llm_config=llm_config
# )

# # create groupchat
# groupchat = autogen.GroupChat(
#     agents=(user_proxy, assistant), messages=[]
# )
# manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

# message = f"""Optimize this resume"""
# user_proxy.initiate_chat(
#         assistant,
#         message=message,
#     )

# message = """
#     I want to develop a resume optimizer. A resume has different sections including the title, executive summary, work experience, \
#     certifications, etc. I think that a good approach would be to output the final result to be a json data that has each of \
#     these components as key and value pairs, for example: \
#     {
#         "optimized_resume": {
#             "title": "software engineer", 
#             "work_exp": [
#                 {
#                     "company_1_name": "lsdkfj", 
#                     "work_description": "a;ldsjf;sd"
#                 }, 
#                 {
#                     "company_2_name": "lsdkfj", 
#                     "work_description": "a;ldsjf;sd"
#                 }
#             ],
#         },
#         "analysis_details": { 
#             "initial_keyword_match_score":42, 
#             "improved_keyword_match_score":78, 
#             "initial_readability_analysis":30, 
#             "improved_readability_analysis":90, 
#             "initial_custom_tailoring":30, 
#             "improved_custom_tailoring":80, 
#             "implemented_improvements": [
#                 "changed tone to be more assertive", 
#                 "used metrics to show impact"
#             ]
#         },
#     }.
# """

# def get_code():
#     # the assistant receives a message from the user_proxy, which contains the task description
#     user_proxy.initiate_chat(
#         assistant,
#         message=message,
#     )

#     # the purpose of the following line is to log the conversation history
#     autogen.ChatCompletion.start_logging()



# # Initialize the agents and group chat manager
# config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")
# parsing_agent = ParsingAgent("parsing_agent", llm_config={"config_list": config_list})
# keyword_matching_agent = KeywordMatchingAgent("keyword_matching_agent", llm_config={"config_list": config_list})
# readability_analysis_agent = ReadabilityAnalysisAgent("readability_analysis_agent", llm_config={"config_list": config_list})
# user_proxy = ResumeOptimizerUserProxy("user_proxy", llm_config={"config_list": config_list})
# group_chat_manager = GroupChatManager("group_chat", [user_proxy, parsing_agent, keyword_matching_agent, readability_analysis_agent])

# # Function to initiate the resume optimization process
# def optimize_resume(resume_text):
#     # Start the conversation with the task description
#     user_proxy.initiate_chat(
#         assistant=parsing_agent,
#         message=json.dumps({
#             "task": "optimize_resume",
#             "resume_text": resume_text
#         })
#     )
#     # The conversation will proceed automatically based on the registered auto-reply functions
#     # and/or LLM-based function calls as per the AutoGen documentation