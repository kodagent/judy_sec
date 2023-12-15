import random

PROPERTY_MAPPINGS = {
        'In Estate': {True: 1, False: 0},
    }

MORTGAGE_PLAN_MAPPINGS = {
        'Property Type': {"House": 0, "Apartment": 1, "Condo": 2},
        'Mortgage Type': {"Bank": 0, "Developer": 1},
    }

USER_PREFERENCE_MAPPINGS = {
        'property_type': {"House": 0, "Apartment": 1, "Condo": 2},
        'mortgage_type': {"Bank": 0, "Developer": 1},
        'in_estate': {True: 1, False: 0}
    }

PROPERTY_COLUMNS = [
    # PROPERTY DATA
    'Property ID',
    'Property Value',
    'Property Size',
    # 'Energy Efficiency',
    'Property Condition',
    # 'Safety & Security',

    # PROPERTY DETAILS DATA
    "Bedrooms",
    "Bathrooms",
    "Living Rooms",
    "Square Footage",
    # "Property Age",
    "In Estate",

    # NEIGHBOURHOOD DATA
    "Number of Nearby Schools",
    "Number of Nearby Hospitals",
    # "Number of Nearby Shopping Centers",
    # "Number of Nearby Parks",
    # "Crime Rate",
    # "Population Density",
    # "Average Income"
]

MORTGAGE_PLAN_COLUMNS = [
    # MORTGAGE PLAN DATA
    "Plan ID",
    'Lender Name',
    "Loan Amount",
    "Loan Term",
    "Interest Rate",
    "Down Payment",
    "Monthly Payment",
    "Property Type",
    # "Customer Rating",
    # 'Min Debt-to-Income Ratio',
    "Mortgage Type",
]

def get_mortgage_description(property_type, area, state, budget, bedrooms, lender_name, loan_amount, loan_term, monthly_payment, interest_rate):
    MORTGAGE_PREDEFINED_RESPONSE_OPTIONS = [
        f"Considering your preferences for a {property_type} in {area}, {state}, with a budget of ₦{budget}, I recommend a mortgage from {lender_name}. With a loan amount of ₦{loan_amount} and a {loan_term}-year term, it aligns with your monthly payment of ₦{monthly_payment}. The interest rate of {interest_rate}% and Bank mortgage type make this an excellent choice.",
        f"For a {bedrooms}-bedroom {property_type} in {area}, {state}, I suggest a mortgage from {lender_name}. The loan amount of ₦{loan_amount} over {loan_term} years at {interest_rate}% interest fits your budget of ₦{budget}. The monthly payments of ₦{monthly_payment} align with your needs.",
        f"I recommend a mortgage from {lender_name} for a {bedrooms}-bedroom {property_type} in {area}, {state}. With a ₦{loan_amount} loan and {loan_term}-year term, it's tailored to your budget of ₦{budget}. The {interest_rate}% interest rate and ₦{monthly_payment} monthly payments offer value.",
        f"For a {property_type} in {area}, {state}, mortgage from {lender_name} is a strong recommendation. With a ₦{loan_amount} loan over {loan_term} years at {interest_rate}% interest, it aligns with your budget of ₦{budget}. The monthly payment of ₦{monthly_payment} is within your reach.",
        f"I highly recommend a mortgage from {lender_name} for a {bedrooms}-bedroom {property_type} in {area}, {state}. With a ₦{loan_amount} loan amount and {loan_term}-year term, it's within your budget of ₦{budget}. The {interest_rate}% interest rate and ₦{monthly_payment} monthly payments are attractive.",
        f"Considering your desire for a {property_type} in {area}, {state}, with 2 bedrooms, I suggest a mortgage from {lender_name}. The loan amount of ₦{loan_amount}, {loan_term}-year term, and {interest_rate}% interest rate fit your budget of ₦{budget}. The ₦{monthly_payment} monthly payments make this a suitable option.",
        f"For your {bedrooms}-bedroom {property_type} preference in {area}, {state}, I recommend a mortgage from {lender_name}. With a ₦{loan_amount} loan over {loan_term} years at {interest_rate}% interest, it aligns with your budget and monthly payment of ₦{monthly_payment}.",
        f"I suggest a mortgage from {lender_name} for a {property_type} in {area}, {state}, within an estate. With a ₦{loan_amount} loan amount and {loan_term}-year term, it fits your budget of ₦{budget}. The {interest_rate}% interest rate and ₦{monthly_payment} monthly payments are affordable.",
        f"Mortgage from {lender_name} is an ideal choice for a {bedrooms}-bedroom {property_type} in {area}, {state}. With a ₦{loan_amount} loan and {loan_term}-year term, it's tailored to your financial situation. The {interest_rate}% interest rate and ₦{monthly_payment} monthly payments offer value.",
        f"For your {property_type} preference in {area}, {state}, within an estate, mortgage from {lender_name} is a top recommendation. With a ₦{loan_amount} loan over {loan_term} years at {interest_rate}% interest, it's within your budget of ₦{budget}. The monthly payment of ₦{monthly_payment} is manageable.",
    ]
    return random.choice(MORTGAGE_PREDEFINED_RESPONSE_OPTIONS)
# async def get_description(content):
#     chat = ChatOpenAI(temperature=0.7, model_name="gpt-4-0613", openai_api_key=settings.OPENAI_API_KEY)
#     messages = [SystemMessage(content="You are a real estate professional."), HumanMessage(content=content),]
#     return chat(messages).content

# async def get_property_description(user_preferences, property_info):
#     property_detail, mortgage_plans_data_raw = property_info

#     user_property_preference = user_property_preference_template.format(
#         user_preferences['bedrooms'],
#         user_preferences['in_estate']
#     )

#     # Create content for property description
#     property_content = f"In less than 100 words, tell the potential client why you would recommend this property to them based on their preference. Property \
#                 Info: {property_detail} {PROPERTY_COLUMNS}, User preferences: {user_property_preference}"

#     # Create tasks for property and mortgage plan descriptions
#     tasks = [get_description(property_content)]
#     for plan in mortgage_plans_data_raw:
#         mortgage_content = f"In less than 50 words, tell the potential client why you would recommend this mortgage plan to them based on their preference. Plan: {plan} {MORTGAGE_PLAN_COLUMNS}, User preference: {user_property_preference}"  # Modify as needed
#         tasks.append(get_description(mortgage_content))

#     # Run all tasks concurrently
#     descriptions = await asyncio.gather(*tasks)

#     property_description = descriptions[0]
#     mortgage_plans_data = [
#         {
#             "mortgage_plan_id": plan[0],
#             "mortgage_plan_lender": plan[1],
#             "mortgage_plan_description": descriptions[i + 1]
#         }
#         for i, plan in enumerate(mortgage_plans_data_raw)
#     ]

#     property_dict = {
#         "property_id": property_detail[0],
#         "property_value": property_detail[1],
#         "property_description": property_description,
#         "mortgage_plans_data": mortgage_plans_data
#     }

#     return property_dict