import os
import time
import uuid

import pinecone
import tiktoken
from decouple import config
from django.conf import settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import S3DirectoryLoader
from more_itertools import chunked

from chatbackend.configs.base_config import openai_client as client
from chatbackend.configs.logging_config import configure_logger

logger = configure_logger(__name__)


pinecone.init(api_key=config("PINECONE_API_KEY"), environment=config("PINECONE_API_ENV"))


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 10
BATCH_SIZE = 50
PINECONE_INDEX_NAME = settings.PINECONE_INDEX_NAME


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
    loader = S3DirectoryLoader(bucket=settings.AWS_STORAGE_BUCKET_NAME, prefix="media/scraped_data/", aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    data = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, length_function=tiktoken_len, separators=["\n\n", "\n", " ", ""])
    texts = text_splitter.split_documents(data)
    return texts

async def create_embedding(text):
    response = client.embeddings.create(
            input=[text],
            model="text-embedding-ada-002"
        )
    text_embedded = response.data[0].embedding
    return text_embedded

async def save_vec_to_database():
    # Initialize Pinecone
    if PINECONE_INDEX_NAME not in pinecone.list_indexes():
        pinecone.create_index(name=PINECONE_INDEX_NAME, metric='cosine', dimension=1536)

    pinecone_index = pinecone.Index(index_name=PINECONE_INDEX_NAME)
    text_chunks = await get_text()
    logger.info("Done getting texts from s3 knowledge store")
    embeddings = []

    for i, chunk in enumerate(text_chunks):
        id = uuid.uuid4().hex
        content_embedded = await create_embedding(chunk.page_content)
        embedding = (id, content_embedded, {"text": chunk.page_content})
        embeddings.append(embedding)
        logger.info(f"Appended embedding chunk {i}")

    # Split the embeddings into smaller chunks (e.g., 50 vectors per request)
    for i, batch in enumerate(chunked(embeddings, BATCH_SIZE)):
        logger.info(f"Uploaded Batch {i}")
        pinecone_index.upsert(batch)

async def query_vec_database(query, num_results):
    start = time.time()
    query_embedding = await create_embedding(query)
    
    pinecone_index = pinecone.Index(index_name=PINECONE_INDEX_NAME)
    results = pinecone_index.query(query_embedding, top_k=num_results, include_metadata=True)
    logger.info(results)
    stop = time.time()
    logger.info(f"QUERY VEC DURATION: {stop - start}")
    
    return results["matches"][0], results["matches"][1]  # , results["matches"][2]

# print(results["matches"][0]['metadata']['text'])
#     print(results["matches"][0]['score'])