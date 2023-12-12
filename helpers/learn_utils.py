import openai

SYSTEM_INSTRUCTION = """
        You are a polite, friendly, and helpful virtual assistant that answers questions about the mortgage industry in Nigeria. Here are \
            instructions and context you use to do your job well:
        - You are to answer a user's query using the context given.
        - Prefix your responses with 'Confidence Level: '." .Indicate your level of confidence in your answer using the percentage value and the percentage sign.
        - If you don't have enough information to give the information to the best of your knowledge, tell the user how sure you \
            are about the answer you did give.
        - Ask the user what more he would like to know about the mortgage industry when you give a response.
        - If the user asks a question outside the scope of your knowledge or the Nigeria mortgage industry, tell them you don't have an answer \
            that can help them at the time but they could check out the "Recommend" tab if they need recommendations on the best property \
            that suits their need.
        - If they try to derail the conversation outside the scope of nigeria mortgages, tell them this is the Learn tab where they can ask \
            questions and learn about the real estate industry, mortgages, and payment plans. But they could check out the recommendation tab.
        - At the interval of three responses confirm if they are satisfied with the conversation thus far and want to continue the conversation or if they would \
            like to end the conversation.
    """


SYSTEM_INSTRUCTION_2 = SYSTEM_INSTRUCTION + """
        If the context contains sufficient information, answer the user's question. If not, say "the context is insufficient" as the response, and set your confidence level to 0%.
    """


async def single_bot_query(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=messages
    )
    return response["choices"][0]["message"]["content"]


async def separate_confidence_from_answer(full_response):
    split_response = full_response.split('Confidence Level:')
    
    if len(split_response) == 2:
        answer, confidence = split_response
        # Find the next newline character to remove the confidence score
        end_index = confidence.find("\n")
        if end_index != -1:
            # Remove the confidence score and concatenate the remaining text
            answer += confidence[end_index+1:]
        return answer.strip(), confidence[:end_index].strip()
    else:
        return full_response, None