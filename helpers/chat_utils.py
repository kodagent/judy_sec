from datetime import date

SYSTEM_INSTRUCTION = """
        You are a polite and friendly virtual assistant. Here are instructions and context you use to do your job well:
        1. You are to get the user to answer 7 questions about the mortgage or property they'd like to buy.
        2. This is the order of questions to help determine the user's preferences: 
            - type of plan, 
            - property State, 
            - property area, 
            - budget, 
            - number of bedrooms, 
            - preferred house type (use only house, apartment and condo as the options for the user and 
                don't ask anymore question on this because those are the only three options we have in the database), 
            - house in an estate or not.
        3. Use the conversation guide below to get the user preferences:
        4. You are to keep the conversation on track even if the user tries to derail the conversation; If he \
            asks a question that shows he wants more information, you respond with "This is the recommend \
            tab where you can receive recommendations for properties you can afford and their associated \
            plans. Would you like to click the learn tab to get more information or continue for me to get \
            your preference and give you the best recommendation?" 
        5. For general questions about the contents in the database, such as property listings or specific attributes, \
        respond with "I'LL VERIFY FROM THE DATABASE"
        6. Do not ask any question twice once it has been answered.        
        7. DO NOT ANSWER ANY QUESTION OUTSIDE THE MORTGAGE INDUSTRY. If such question is asked, tell the user that you are only supposed \
            to focus on the mortgage industry because that's all you know about!

        ## CONVERSATION GUIDE STARTS ##
        User prompt: What kind of mortgage can I get?
        Bot response: There are two types of plans you can get on Giddaa:
        
        Bank Mortgage Plans: Long-term plans with interest rates ranging from 6% to 22%.
        Pros:
        - Total payments are made over a long period, allowing small monthly payments.
        - Low down payments (0% to 20%).
        Cons:
        - Interest rates increase the total cost of the property.
        - Affordability analysis is required.
        
        Developer Payment Plans: Short-term plans with 0% interest.
        Pros:
        - No interest on the property.
        - No rigorous financial analysis.
        Cons:
        - Requires larger down payments (20% to 50%).
        - Total payments must be made over a short period.
        
        Which plan would you prefer?
        
        User prompt: Developer Payment Plans
        Bot response: What State are you looking to get the property?

        User prompt: Lagos
        Bot response: What area are you looking to get the property?

        User prompt: Festac
        Bot response: Great! What is your budget for this property?
        
        User prompt: 300000
        Bot response: How many bedrooms are you looking for?
        
        User prompt: 5
        Bot response: Do you have a preferred house type? Select one (e.g., House, Apartment, Condo)
        
        User prompt: A house is fine.
        Bot response: Good choice! Do you want the house to be in an estate or not?
        ## CONVERSATION GUIDE STOPS ##
        
        Lastly, When you have asked all required questions above in the conversation guide, make the function call to get_user_preferences.

        P.S. If you have given the user a recommendation but the user wants to continue the conversation by asking another question, \
        go ahead to start the conversation again using the conversation guide and at the end this time use the user's newest preferences \
        for the next function call.
    """

APARTMENT_TYPE = ["Aparment", "House", "Condo"]
MORTGAGE_TYPE = ["Bank", "Developer"]

FUNCTIONS_PARAMS = [
    {
        "name": "get_user_preferences",
        "description": "Gets the user preferences from conversation texts",
        "parameters": {
            "type": "object",
            "properties": {
                "area": {
                    "type": "string",
                    "description": "Sentence case of area where the desired property is located"
                },
                "state": {
                    "type": "string",
                    "description": "Sentence case of State where the desired property is located"
                },
                "budget": {
                    "type": "integer",
                    "description": "The user's budget for the desired property in numeric figures"
                },
                "bedrooms": {
                    "type": "integer",
                    "description": "The number of bedrooms the user wants in the desired property in numeric figures"
                },
                "in_estate": {
                    "type": "boolean",
                    "description": "Python Boolean value to show if the user wants the property to be in an estate or not. True for affirmative or yes and False for negative or no"
                },
                "property_type": {
                    "type": "string",
                    "description": f"A Sentence case keyword such as {APARTMENT_TYPE[0]}, {APARTMENT_TYPE[1]} or {APARTMENT_TYPE[2]}"
                },
                "mortgage_type": {
                    "type": "string",
                    "description": f"A Sentence case keyword such as {MORTGAGE_TYPE[0]} or {MORTGAGE_TYPE[1]}"
                }
            }
        }
    }
]


EMPLOYMENT_VERIFICATION_INSTRUCTION = """
    You are a help assistant that helps get the required entities from an employment letter.
"""


EMPLOYMENT_LETTER_FUNCTIONS_PARAMS = [
    {
        "name": "get_employment_letter_entities",
        "description": "Gets entities from the contents in the employment letter. Return 'None' keyword for entity param that does not exist in the employment letter provided.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": f"The start date for the employee."
                },
                "current_staff": {
                    "type": "boolean",
                    "description": f"Looking at the current date it returns True if the employee still works in the organization and False if not. Current date: {date.today()}"
                },
                "job_role": {
                    "type": "string",
                    "description": f"The job role of the employee"
                },
                "salary": {
                    "type": "string",
                    "description": "The salary value offered to the employee in numeric figures. Example: {currency_symbol}200000"
                },
                "company_name": {
                    "type": "string",
                    "description": "The name of the company offering the employment"
                },
                "representative": {
                    "type": "string",
                    "description": "The name of the company representative"
                },
                "representative_position": {
                    "type": "string",
                    "description": "The position of the company representive. Return Python Boolean False if it does not exist"
                },
                "representative_email": {
                    "type": "string",
                    "description": "The email of the company representive. Return Python Boolean False if it does not exist"
                },
                "representative_phone_number": {
                    "type": "string",
                    "description": "The phone number of the company representive. Return Python Boolean False if it does not exist"
                },
                "company_website": {
                    "type": "string",
                    "description": "Company website url. Return Python Boolean False if it does not exist"
                },
            }
        }
    }
]


WEBSITE_EMAIL_FUNCTIONS_PARAMS = [
    {
        "name": "get_website_emails",
        "description": "Gets the emails from the website contents",
        "parameters": {
            "type": "object",
            "properties": {
                "found_organization_email": {
                    "type": "boolean",
                    "description": f"True for if organization email is found otherwise False"
                },
                "organization_email": {
                    "type": "string",
                    "description": f"email of the organization"
                },
                "found_personel_email": {
                    "type": "boolean",
                    "description": f"True for if personel email is found otherwise False"
                },
                "personel_email": {
                    "type": "string",
                    "description": f"email of the personel"
                },
                "personel_role": {
                    "type": "string",
                    "description": f"role of the personel in the organization"
                },
            },
        },
    },
    {
        "name": "identify_closest_hr_role",
        "description": "Identifies the email of the person with the role closest to HR from a given list",
        "parameters": {
            "type": "object",
            "properties": {
                "email_list": {
                    "type": "array",
                    "description": "List of emails and roles in JSON format",
                    "items": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string"},
                            "role": {"type": "string"}
                        }
                    }
                },
                "closest_hr_email": {
                    "type": "string",
                    "description": "Email of the person with the role closest to HR"
                },
                "closest_hr_role": {
                    "type": "string",
                    "description": "Role of the person closest to HR"
                }
            }
        }
    }
]


BANK_STATEMENT_VERIFICATION_INSTRUCTION = """
    You are a help assistant that helps get the data from a bank statement and return it in a json readable format. You help get the insights in the bank statement document.
"""


BANK_DATA_COLLATION_VERIFICATION_INSTRUCTION = """
    you are a very intelligent mathematician that doesn't fail any addition or subtraction.  You check your calculations one by one to ensure that you are \
    not making any mistakes or oversights.
    
    Task to do:
    - Calculate the total income, total expenses from the given table: 
    - Convert the month numerical value to the Month Name using the provided month mapping:

    Month Mapping:
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'

    Sample Table:
        | Year | Month | Expenses | Income   |
        |------|-------|----------|----------|
        | 2023 | 1     | 22025.0  | 100000.0 |
        | 2023 | 1     | 142329.35| 82000.0  |
        | 2023 | 1     | 26660.73 | 10000.0  |
        | 2023 | 1     | 23010.75 | 24000.0  |

    Sample Result:
        {'year': '2023', 'month': 'January', 'total_income': 214025.83, 'total_expenses': 216000.0}
"""


BANK_DATA_COLLATION_FUNCTIONS_PARAMS = [
    {
        "name": "get_data_collation",
        "description": "Gets the total income, total expenses, total_savings, average_savings ratio from the dataframe results in the given texts",
        "parameters": {
            "type": "object",
            "properties": {
                "year": {
                    "type": "string",
                    "description": f"The year in which the transactions occured in."
                },
                "month": {
                    "type": "string",
                    "description": f"The name of the month in which the transactions occured in. Example: January"
                },
                "total_income": {
                    "type": "integer",
                    "description": f"Adds up all the values in the income column."
                },
                "total_expenses": {
                    "type": "integer",
                    "description": f"Adds up all the values in the expenses column."
                },
                # "total_savings": {
                #     "type": "integer",
                #     "description": f"Adds up all the savings values in the various dataframe."
                # },
                # "average_savings_ratio": {
                #     "type": "integer",
                #     "description": f"This is the value gotten from the calculation: total_savings/total_income * 100"
                # },
            },
            "required": ["year", "month", "total_income", "total_expenses"]
        },
    },
]


BANK_STATEMENT_COLUMN_INSTRUCTION = "You are a chatbot that gets the column names from the text description from a bank statement dataframe. if the names are not close in meaning to DATE, CREDIT, DEBIT, DESCRIPTION, then discard them as None"


BANK_STATEMENT_COLUMN_FUNCTIONS_PARAMS = [
    {
        "name": "get_column_names",
        "description": "Get the column names of the dataframe in the bank statement file",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "The name of the column for dates of transaction. Return None if it doesn't exist"
                },
                "date_index": {
                    "type": "integer",
                    "description": "The index of the column for dates of transaction. Return None if it doesn't exist"
                },
                "income": {
                    "type": "string",
                    "description": "The name of the column that shows income coming into the account. Return None if it doesn't exist"
                },
                "income_index": {
                    "type": "integer",
                    "description": "The index of the column that shows income coming into the account. Return None if it doesn't exist"
                },
                "expense": {
                    "type": "string",
                    "description": "The name of the column that shows expenses. Return None if it doesn't exist"
                },
                "expense_index": {
                    "type": "integer",
                    "description": "The index of the column that shows expenses. Return None if it doesn't exist"
                },
                "description": {
                    "type": "string",
                    "description": "The name of the column that describes the transaction. Return None if it doesn't exist"
                },
                "description_index": {
                    "type": "integer",
                    "description": "The index of the column that describes the transaction. Return None if it doesn't exist"
                },
            },
            "required": ["date", "income", "expense", "description", "date_index", "income_index", "expense_index", "description_index"]
        },
    }
]

