def get_resume_instruction(job_role, section):
    SYSTEM_INSTRUCTION = f"""
        You are a professional recruiter that helps individuals optimize their resumes. \
        Take a look at the content of this resume and optimize the {section} for this job role: {job_role}
    """
    return SYSTEM_INSTRUCTION


async def get_resume_parser_instruction(section):
    SYSTEM_INSTRUCTION = f"""
        You are a helper assistant that helps with detailed resume parsing. Extract and return only the text in the resume. Do not write any additional text\
        Take a look at the content of this resume and extract the contents of section: {section}. if section doesn't exist return None
    """
    return SYSTEM_INSTRUCTION


# def get_cover_letter_instruction(job_role):
#     SYSTEM_INSTRUCTION = f"""
#         You are a professional recruiter that helps individuals optimize their cover letters. \
#         Take a look at the content of this cover letter and optimize it to get the best result for this job role: {job_role}
#     """
#     return SYSTEM_INSTRUCTION


def get_job_post_instruction(job_role):
    SYSTEM_INSTRUCTION = f"""
        You are a professional recruiter that helps recruiters optimize their job post. \
        Take a look at the content of this job post and optimize it to get the best result for the job role: {job_role}
    """
    return SYSTEM_INSTRUCTION


job_post_description = f"""
Job Title: Staff Software Engineer (ML/AI) - Remote

About the job
We're Plentific, the world’s leading real-time property solution, and we're looking for top talent to join our ambitious team. We’re a global company, headquartered in London, and operating across the United Kingdom, Germany and North America.


As a B2B company, we're dedicated to helping landlords, letting agents and property managers streamline operations, unlock revenue, increase tenant satisfaction, and remain compliant through our award-winning SaaS technology platform. We also work with SMEs and large service providers, helping them access more work and grow their businesses.


We're not just any proptech - we're backed by some of the biggest names in the business, including A/O PropTech, Highland Europe, Mubadala, RXR Digital Ventures and Target Global and work with some of the world’s most prominent real estate players.


But we're not just about business - we're also building stronger communities where people can thrive by ensuring the quality and safety of buildings, supporting decarbonisation through our ESG Retrofit Centre of Excellence and championing diversity across the sector through the Women’s Trade Network. We're committed to creating exceptional experiences for our team members, too. Our culture is open and empowering, and we're always looking for passionate, driven individuals to join us on our mission.


So, what's in it for you?


A fast-paced, friendly, collaborative and hybrid/flexible working environment
Ample opportunities for career growth and progression
A multicultural workplace with over 20 nationalities that value diversity, equity, and inclusion
Prioritisation of well-being with social events, digital learning, career development programs and much more


If you're ready to join a dynamic and innovative team that’s pioneering change in real estate, we'd love to hear from you.


The Role


This is a fully remote position based anywhere in the UK.


We are looking for an experienced Staff Software Engineer to join the Data Engineering team. You'll be reporting to the Head of Data Engineering and will have responsibility across large production code bases and will also be tasked with software architecture designs and reviews. The role is heavy hands-on coding, as an individual contributor, with no people management responsibilities, though you will be expected to enjoy mentoring other engineers.


The Data Engineering team, alongside the Frontend, Backend and DevOps teams, sits at the centre of everything we do at Plentific and is constantly tackling challenging problems, such as online payments, quoting, invoicing, booking, search / scoring algorithms, ETL, data pipelines, in-app messaging, Public APIs, ML/AI, real-time notifications and fraud prevention.


The team has a stronger focus and ownership of the production Machine Learning systems, the data warehouse, Public APIs, real-time data pipelines, LLM's and AI in general, and our flagship interactive analytics module named 'Advanced Analytics'. Almost all code so far is written in Python and SQL.


Our tech stack is made of, amongst others: AWS, Kubernetes, Django, PostgreSQL, Snowflake, ElasticSearch, dbt, Looker, scikit-learn, FastAPI, Celery, Jenkins, GitHub.


Responsibilities


Be the main individual contributor to the most strategic and high impact projects in Plentific
Own and defend the software architecture designs from conception to release, including build vs buy discussions
Collaborate with Product stakeholders, to understand, define, develop and implement scalable, cutting-edge solutions that amaze our customers
Serve as a tech lead to look up to, providing guidance and mentorship to help develop the skills and talents of others
Champion best coding practices, documentation, reviews, unit and integrations testing, data quality and security, and performance


Requirements


Skills


Excellent Python and SQL skills, but you should be open to picking up other programming languages
A strong interest in learning and developing AI-powered systems (such as LLM-based)
A self-starter who assumes responsibility for their work, accepts direction and feedback from co-workers and managers, and happily helps make anyone’s good idea a reality
Ability to think out of the box with a can-do attitude to get things done efficiently
Excellent communication skills in English


Experience And Qualifications


7+ years of relevant experience as a Software Engineer
Experience with Machine Learning is a must, since we are heavily expanding our capabilities in this area


Benefits


As you can see, we are quickly progressing with our ambitious plans and are eager to grow our team of doers to achieve our vision of managing over 2 million properties through our platform across various countries. You can help us shape the future of property management across the globe. Here’s what we offer:


A competitive compensation package
A flexible working environment + 25 days annual holiday
Private health care including discounted gym membership
Enhanced parental leave
Life insurance
Employee assistance program
Company volunteering day and charity salary sacrifice scheme
Learning management system by SAP Litmos
Learning and development fund
Referral bonus and charity donation if someone you introduce joins the company
Season ticket loan, Cycle to work, Electric vehicle and Techscheme programs
Pension - 3% employer contribution, 5% employee contribution
Lunch of your choice once a week for office based employees
Regular company-sponsored lunches, dinners and social gatherings
Fully stocked kitchen with drinks, snacks, fruit, breakfast cereal etc
"""

cover_letter = f"""
Application for Staff Software Engineer (ML/AI) Position - Daniel Nwachukwu

Dear Hiring Manager,

I am writing to express my interest in the Staff Software Engineer (ML/AI) position at Plentific, as advertised. With a solid background in software engineering, specializing in Machine Learning and Artificial Intelligence, and over 4 years of professional experience, I am excited about the opportunity to contribute to Plentific’s innovative solutions in real-time property management. My resume is attached for your consideration.

My experience as an AI Developer at Gidaa and Essential Recruit has provided me with a strong foundation in developing and deploying ML/AI-powered applications, aligning perfectly with the requirements of this role. At Gidaa, I engineered an advanced recommendation system to tailor properties and mortgage plans to users, which increased customer satisfaction by 25%. Furthermore, at Essential Recruit, I developed an AI application for job recommendations using candidate data and preferences, which pushed up job acquisition rate by 60%.

Moreover, my tenure at Project School and DFX Gadgets Hub allowed me to hone my backend and full stack development skills, respectively. My contributions ranged from improving server-side architecture, implementing API versioning, to enhancing security measures which in turn, significantly improved overall application performance and user satisfaction.

Having reviewed Plentific’s mission and the job description, I am particularly drawn to your commitment to building stronger communities and ensuring the quality and safety of buildings through award-winning SaaS technology platform. I am excited about the chance to contribute to high-impact projects, collaborate with a multicultural team, and further hone my skills in AI and Machine Learning, while also mentoring other engineers as indicated in the job description.

I am adept at Python, SQL, and have a proven track record in developing and deploying ML/AI systems using TensorFlow, Keras, and Scikit-Learn amongst other technologies. I believe my strong problem-solving ability, excellent communication skills in English, and a proactive approach make me a great fit for this role. The prospect of working remotely yet being an integral part of a dynamic, innovative team like Plentific's is thrilling, and I am eager to contribute to your ongoing and future projects, aiding in the continuous growth and success of Plentific.

Thank you for considering my application. I am looking forward to the opportunity to further discuss how I can contribute to your team. I am open to providing any additional information or references as needed, and I am hopeful for a chance to discuss my application in an interview setting.

Warm regards,

Daniel Nwachukwu
contactugodaniels@gmail.com
+2347033588400
LinkedIn: https://www.linkedin.com/in/ugo-nwachukwu
"""


llm_config_test = {
    "functions": [
        {
            "name": "extract_keywords_text_from_job_description",
            "description": "extracts skills, technologies, qualifications sections from job description content to be used for keyword matching",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_description": {
                        "type": "string",
                        "description": "job description content",
                    },
                },
                "required": ["job_description"],
            },
        },
        {
            "name": "keyword_analysis",
            "description": "matches keywords in resume content with keywords extracted from job description to output matching keywords and a matching score",
            "parameters": {
                "type": "object",
                "properties": {
                    "resume_text": {
                        "type": "string",
                        "description": "content of the resume",
                    },
                    "job_description_keywords_section": {
                        "type": "string",
                        "description": "extracted skills, technologies, qualifications section text from job description content",
                    },
                },
                "required": ["resume_text", "job_description_keywords_section"],
            },
        },
        {
            "name": "readability_analysis",
            "description": "analyses the complexity and readability of the resume text and returns a complexity score and readability score. Uses textstat.flesch_kincaid_grade and textstat.flesch_reading_ease to achieve this",
            "parameters": {
                "type": "object",
                "properties": {
                    "resume_text": {
                        "type": "string",
                        "description": "content of the resume",
                    },
                },
                "required": ["resume_text"],
            },
        },
        # {
        #     "name": "get_readability_text",
        #     "description": "takes the complexity score and readability score and converts the figures into readable text",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "fk_score": {
        #                 "type": "integer",
        #                 "description": "complexity score"
        #             },
        #             "fre_score": {
        #                 "type": "integer",
        #                 "description": "readability score"
        #             },
        #         },
        #         "required": ["fk_score", "fre_score"]
        #     },
        # },
        {
            "name": "resume_parser",
            "description": "Parse resume into sections: Contact Information, Objective/Summary, Experience, Education, Skills, Certifications, Projects, References",
            "parameters": {
                "type": "object",
                "properties": {
                    "resume_text": {"type": "string", "description": "Resume content"},
                },
                "required": ["resume_text"],
            },
        },
        {
            "name": "get_section_feedback",
            "description": "Get feedback on each section: Contact Information, Objective/Summary, Experience, Education, Skills, Certifications, Projects, References",
            "parameters": {
                "type": "object",
                "properties": {
                    "section_name": {
                        "type": "string",
                        "description": "name of section",
                    },
                    "section_content": {
                        "type": "string",
                        "description": "content of section",
                    },
                },
                "required": ["section_name", "section_content"],
            },
        },
        {
            "name": "provide_complete_feedback",
            "description": "provide final feedback using the section feedback, complexity score, readability score and matching keywords",
            "parameters": {
                "type": "object",
                "properties": {
                    "matching_keywords": {
                        "type": "string",
                        "description": "list of matching keywords separated by commas",
                    },
                    "complexity_score": {
                        "type": "integer",
                        "description": "the complexity score of the resume content",
                    },
                    "readability_score": {
                        "type": "integer",
                        "description": "the readability score of the resume content",
                    },
                    "section_feedback": {
                        "type": "object",
                        "description": "a dictionary of section names as keys and section content as values. This dictionary is gotten from using the resume_parser function",
                    },
                },
                "required": [
                    "matching_keywords",
                    "complexity_score",
                    "readability_score",
                    "section_feedback",
                ],
            },
        },
        {
            "name": "optimize_resume",
            "description": "uses the resume content, job description and resume feedback to optimize the resume",
            "parameters": {
                "type": "object",
                "properties": {
                    "resume_content": {
                        "type": "string",
                        "description": "the content of the resume",
                    },
                    "job_description": {
                        "type": "string",
                        "description": "the job description content",
                    },
                    "resume_feedback": {
                        "type": "string",
                        "description": "the feedback on the resume",
                    },
                },
                "required": ["resume_content", "job_description", "resume_feedback"],
            },
        },
        # {
        #     "name": "score_job_role",
        #     "description": """Evaluates job role in a company with a score of (1 to 10) based on these metrics:
        #         1. Patient Outcomes
        #         2. Process Improvements
        #         3. Cost Management
        #         4. Team Management
        #         5. Certifications
        #         6. Patient Satisfaction""",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "role_description": {
        #                 "type": "string",
        #                 "description": "the work experience in a particular organization"
        #             },
        #         },
        #         "required": ["role_description"]
        #     },
        # },
        # {
        #     "name": "score_impact",
        #     "description": "Takes in impact dictionary and calculates a total impact score in job role.",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "impact_dict": {
        #                 "type": "object",
        #                 "description": """Analysis of the impact of the candidate in certain areas in a particular role on a scale of 1 to 10
        #                     SAMPLE IMPACT DICTIONARY
        #                     {
        #                         'patient_outcomes': 5,
        #                         'process_improvements': 7,
        #                         'cost_management': 2,
        #                         'team_management': 7,
        #                         'certifications': 3,
        #                         'patient_satisfaction': 8
        #                     }"""
        #             },
        #         },
        #         "required": ["impact_dict"]
        #     },
        # },
    ]
}

llm_config_general_optimizer = {
    "functions": [
        {
            "name": "optimize_resume",
            "description": "uses the resume content, job description and resume feedback to optimize the resume",
            "parameters": {
                "type": "object",
                "properties": {
                    "resume_content": {
                        "type": "string",
                        "description": "the content of the resume",
                    },
                    "job_description": {
                        "type": "string",
                        "description": "the job description content",
                    },
                    "resume_feedback": {
                        "type": "string",
                        "description": "the feedback on the resume",
                    },
                },
                "required": ["resume_content", "job_description", "resume_feedback"],
            },
        },
    ]
}
