import os
import time
import uuid

import pinecone
import tiktoken
from decouple import config
from django.conf import settings
from langchain.document_loaders import GCSDirectoryLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain_community.document_loaders import S3DirectoryLoader
from more_itertools import chunked
from openai import OpenAI

from chatbackend.logging_config import configure_logger

logger = configure_logger(__name__)


client = OpenAI()
pinecone.init(api_key=config("PINECONE_API_KEY"), environment=config("PINECONE_API_ENV"))

# ------------------------ UTIL FUNCTIONS ----------------------
async def get_text():
    def tiktoken_len(text):
        # Tokenize and split text
        tokenizer = tiktoken.get_encoding('cl100k_base')
        tokens = tokenizer.encode(
            text,
            disallowed_special=()
        )
        return len(tokens)
    
    # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = auth_json_path

    # this was removed to rely on the settings.py configuration, double check that it is still working
    # decoded_credentials = base64.b64decode(settings.GOOGLE_APPLICATION_CREDENTIALS).decode()
    # credentials_data = json.loads(decoded_credentials)
    # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_data

    # Load data
    # loader = GCSDirectoryLoader(project_name=os.getenv('GAE_PROJECT_NAME'), bucket=os.getenv('GS_BUCKET_NAME'))
    loader = S3DirectoryLoader("testing-hwc", aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    data = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=10, length_function=tiktoken_len, separators=["\n\n", "\n", " ", ""])
    texts = text_splitter.split_documents(data)
    return texts

async def create_embedding(text):
    response = client.embeddings.create(
            input=[text],
            model="text-embedding-ada-002"
        )
    text_embedded = response["data"][0]["embedding"]
    return text_embedded

async def save_vec_to_database(pinecone_index_name):
    # Initialize Pinecone
    # pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_API_ENV"))
    if pinecone_index_name not in pinecone.list_indexes():
        pinecone.create_index(name=pinecone_index_name, metric='cosine', dimension=1536)

    pinecone_index = pinecone.Index(index_name=pinecone_index_name)
    text_chunks = await get_text()
    embeddings = []

    for chunk in text_chunks:
        id = uuid.uuid4().hex
        content_embedded = await create_embedding(chunk.page_content)
        embedding = (id, content_embedded, {"text": chunk.page_content})
        embeddings.append(embedding)

    # Split the embeddings into smaller chunks (e.g., 50 vectors per request)
    for batch in chunked(embeddings, 50):
        pinecone_index.upsert(batch)

async def query_vec_database(query, num_results, pinecone_index_name):
    start = time.time()
    query_embedding = await create_embedding(query)
    
    pinecone_index = pinecone.Index(index_name=pinecone_index_name)
    results = pinecone_index.query(query_embedding, top_k=num_results, include_metadata=True)

    stop = time.time()
    logger.info(f"QUERY VEC DURATION: {stop - start}")
    
    return results["matches"][0], results["matches"][1]  # , results["matches"][2]

# print(results["matches"][0]['metadata']['text'])
#     print(results["matches"][0]['score'])