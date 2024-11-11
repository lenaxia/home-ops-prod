#!/usr/bin/env python

import random
import time
from dateutil import parser
from datetime import datetime
import re
import tempfile
import os
import json
import logging
from PIL import Image
import base64
import requests
import sys
import fitz  # PyMuPDF
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
PAPERLESS_HOST = 'http://paperless.storage.svc.cluster.local:80/api'
PAPERLESS_API_KEY = os.getenv('PAPERLESS_APIKEY')
OPENAI_API_KEY = os.getenv('OPENAI_APIKEY')
#OPENAI_API_ENDPOINT = "https://api.openai.com"
OPENAI_API_ENDPOINT = "http://localai.home.svc.cluster.local:8080"

# OpenAI Model Configuration
ENABLE_VISION = False
VISION_MODEL = "bedrock-claude-v2-sonnet"
VISION_MODEL_TOKENS_MAX = 200000
TEXT_MODEL = "bedrock-claude-v2-sonnet"
TEXT_MODEL_TOKENS_MAX = 200000
MAX_RETURN_TOKENS = 4096

# Import LangChain and LangGraph components
from langchain.llms import OpenAIChat
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.indexes import VectorstoreIndexCreator
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import VectorDBQAWithSourcesChain
from langchain.chains.summarize import load_summarize_chain
from langchain.chains.question_answering import load_qa_chain
from langchain.document_transformers import PDFFormDataExtractor
from langchain.image_utils import load_image
from langchain.prompts.prompt import PromptTemplate
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.tools.file_management.utils import (
    LocalFileURLReader,
    LocalFileToolsSummarize,
    LocalFileToolsOCR,
)
from pydantic import BaseModel, Field

# LangChain model and embeddings
llm = OpenAIChat(
    temperature=0, openai_api_key=OPENAI_API_KEY, model_name=TEXT_MODEL
)
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

def fetch_tags():
    url = f'{PAPERLESS_HOST}/tags/'
    return fetch_metadata_list(url)

def fetch_correspondents():
    url = f'{PAPERLESS_HOST}/correspondents/'
    return fetch_metadata_list(url)

def fetch_document_types():
    url = f'{PAPERLESS_HOST}/document_types/'
    return fetch_metadata_list(url)

def fetch_metadata_list(url):
    headers = {"Authorization": f"Token {PAPERLESS_API_KEY}"}
    all_data = []

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', data) if isinstance(data, dict) else data
            all_data.extend(results)

            # Check if there is a next page
            url = data.get('next', None)  # 'next' will be the URL for the next page if it exists
        else:
            logger.error(f"Failed to fetch metadata from {url}. Status code: {response.status_code}")
            break  # Exit the loop if an error occurs

    return all_data

def fetch_metadata():
    metadata = {
        "tags": fetch_metadata_list(f'{PAPERLESS_HOST}/tags/'),
        "correspondents": fetch_metadata_list(f'{PAPERLESS_HOST}/correspondents/'),
        "document_types": fetch_metadata_list(f'{PAPERLESS_HOST}/document_types/')
    }
    return metadata

def download_document(document_id):
    url = f'{PAPERLESS_HOST}/documents/{document_id}/'
    logger.info(f"Downloading document from: {url}")
    headers = {"Authorization": f"Token {PAPERLESS_API_KEY}"}
    response = requests.get(url, headers=headers)
    logger.info(f"Status code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        content_type = data.get('content_type', '')
        return content_type, data
    else:
        logger.error(f"Failed to download document. Status code: {response.status_code}")
        return None, None

def resize_image(image_path, max_length=2048):
    try:
        with Image.open(image_path) as img:
            ratio = max_length / max(img.size)
            new_size = tuple([int(x * ratio) for x in img.size])
            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
            resized_img.save(image_path)
        return image_path
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        return None

# Use LangChain's VisionAndLanguage model for OCR
from langchain.vision import VisionAndLanguage
vision_and_language = VisionAndLanguage(
    vision_llm=OpenAIChat(
        temperature=0, openai_api_key=OPENAI_API_KEY, model_name=VISION_MODEL
    ),
    vision_text_max_tokens=VISION_MODEL_TOKENS_MAX,
)

def ocr_document(image_path, debug=False):
    retry_wait = 5  # Initial backoff wait time in seconds
    max_retries = 8
    for attempt in range(max_retries):
        try:
            resized_image_path = resize_image(image_path)
            if not resized_image_path:
                return None

            image = load_image(resized_image_path)
            ocr_text = vision_and_language.get_text(image)
            return ocr_text

        except Exception as e:
            logger.error(f"Error during OCR request: {e}")
            if attempt < max_retries - 1:
                retry_wait = 2 ** attempt + random.uniform(0, 1)
                logger.error(f"Retrying in {retry_wait} seconds...")
                time.sleep(retry_wait)
            else:
                logger.error("Max retries exceeded for OCR document request")
                return None

# Define a Pydantic model for document classification
class DocumentClassification(BaseModel):
    creation_date: str = Field(None, description="The date the document was created")
    tag: list[str] = Field([], description="List of tags for the document")
    correspondent: str = Field(None, description="The correspondent for the document")
    document_type: str = Field(None, description="The type of document")
    title: str = Field(None, description="The title for the document")

# Load the classification prompt
with open("classification_prompt.txt", "r") as f:
    classification_prompt = f.read()

# Create a prompt template for document classification
classification_template = PromptTemplate(
    input_variables=["ocr_text", "tags", "correspondents", "document_types"],
    template=classification_prompt,
)

# Function to classify documents using LangChain
def classify_document(
    ocr_text,
    tags,
    correspondents,
    document_types,
    image_path=None,
    max_tokens=MAX_RETURN_TOKENS,
    debug=False,
):
    tags_str = ", ".join([f"'{tag['name']}'" for tag in tags])
    correspondents_str = ", ".join([f"'{correspondent['name']}'" for correspondent in correspondents])
    document_types_str = ", ".join([f"'{doc_type['name']}'" for doc_type in document_types])

    prompt = classification_template.format(
        ocr_text=ocr_text,
        tags=tags_str,
        correspondents=correspondents_str,
        document_types=document_types_str,
    )

    if image_path:
        image = load_image(image_path)
        response = vision_and_language.classify(prompt, image, max_tokens=max_tokens)
    else:
        response = llm(prompt, max_tokens=max_tokens)

    try:
        classification_data = DocumentClassification.parse_raw(response)
        return classification_data
    except Exception as e:
        logger.error(f"Error parsing classification data: {e}")
        return None

def extract_classification_data(classification_result):
    return classification_result

def update_document_content(document_id, ocr_text, classification_result, tags, correspondents, document_types):
    # Extract the classification data
    classification_data = classification_result

    # Find the IDs for the tags, correspondent, and document type
    tag_ids = []
    for tag_name in classification_data.tag:
        tag_id = next((tag['id'] for tag in tags if tag['name'] == tag_name), None)
        if tag_id:
            tag_ids.append(tag_id)

    if 111 not in tag_ids:
        tag_ids.append(111)
    if 112 not in tag_ids:
        tag_ids.append(112)

    correspondent_id = next((correspondent['id'] for correspondent in correspondents if correspondent['name'] == classification_data.correspondent), None)
    document_type_id = next((doc_type['id'] for doc_type in document_types if doc_type['name'] == classification_data.document_type), None)

    # Convert the creation date to the correct format using dateutil
    creation_date = classification_data.creation_date
    if creation_date:
        try:
            parsed_date = parser.parse(creation_date)
            iso_date = parsed_date.strftime("%Y-%m-%dT00:00:00Z")  # Assuming time is not provided
        except ValueError as e:
            logger.error(f"Date parsing error: {e}")
            iso_date = ''
    else:
        iso_date = ''

    # Prepare the initial payload
    payload = {
        "created": iso_date,
        "tags": tag_ids,
        "correspondent": correspondent_id,
        "document_type": document_type_id,
        "title": classification_data.title
    }

    # Add "content" to payload only if ocr_text does not contain the specific message
    detected_phrases = ["I can't assist with that request.", "I'm sorry"]

    if not any(phrase in ocr_text for phrase in detected_phrases):
        payload["content"] = ocr_text
    else:
        logger.info("LLM unable to comply with OCR request")

    # Remove keys with empty string values from payload
    payload = {k: v for k, v in payload.items() if v != ''}

    url = f'{PAPERLESS_HOST}/documents/{document_id}/'
    headers = {"Authorization": f"Token {PAPERLESS_API_KEY}", "Content-Type": "application/json"}
    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code == 200:
        logger.info(f"Document content updated successfully for document ID {document_id}.")
    else:
        logger.error(f"Failed to update document content for document ID {document_id}. Status code: {response.status_code}")
        logger.error(f"Response text: {response.text}")

def main(document_id, debug=False):
    if debug:
        logger.setLevel(logging.DEBUG)

    # Fetch metadata for classification
    tags = fetch_tags()
    correspondents = fetch_correspondents()
    document_types = fetch_document_types()

    content_type, document_metadata = download_document(document_id)
    if not document_metadata:
        logger.error("Failed to download document.")
        return

    file_content = document_metadata.get('content', '').encode('utf-8')

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(file_content)
        tmp_file_path = tmp_file.name

    # OCR and classify the document
    ocr_text, classification_result = process_document(
        tmp_file_path, content_type, tags, correspondents, document_types, debug
    )

    if ocr_text and classification_result:
        logger.info(f"Classification Result: {classification_result}")
        update_document_content(
            document_id, ocr_text, classification_result, tags, correspondents, document_types
        )
    else:
        logger.warning("No OCR text or classification result found.")

    # Clean up the temporary file
    os.remove(tmp_file_path)

    logger.info("Run complete")

def process_document(
    file_path, content_type, tags, correspondents, document_types, debug=False
):
    # Initialize an empty list to collect OCR text from all pages
    aggregated_ocr_text = []
    classification_result = None

    # OCR the document if it is a PDF and contains only images
    if content_type == 'application/pdf' and is_pdf_image_only(file_path) and ENABLE_VISION:
        logger.info("PDF contains only images, extracting for OCR...")
        with fitz.open(file_path) as doc:
            for page_number in range(len(doc)):
                page = doc.load_page(page_number)
                pix = page.get_pixmap()
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as img_file:
                    pix.save(img_file.name)
                    ocr_text = ocr_document(img_file.name, debug)
                    if ocr_text:
                        aggregated_ocr_text.append(ocr_text)

                        # Perform classification only on the first page
                        if page_number == 0:
                            classification_result = classify_document(
                                ocr_text, tags, correspondents, document_types, img_file.name, debug=debug
                            )

        # After all pages have been processed, join the OCR text
        if aggregated_ocr_text:
            full_ocr_text = "\n".join(aggregated_ocr_text)
            return full_ocr_text, classification_result

    # Handle image documents
    elif content_type in ['image/jpeg', 'image/png'] and ENABLE_VISION:
        logger.info("Image file detected, processing with OCR...")
        ocr_text = ocr_document(file_path, debug)
        if ocr_text:
            classification_result = classify_document(
                ocr_text, tags, correspondents, document_types, file_path, debug=debug
            )
            return ocr_text, classification_result

    # Handle other document types (fallback)
    else:
        ocr_text = document_metadata.get('content', '')
        classification_result = classify_document(
            ocr_text, tags, correspondents, document_types, debug=debug
        )
        return ocr_text, classification_result

    # If no OCR text or classification result is found
    return None, None

if __name__ == "__main__":
    # Check if document ID is provided as a command-line argument
    if len(sys.argv) > 1:
        document_id = sys.argv[1]
    else:
        # Check if DOCUMENT_ID environment variable is set
        document_id = os.getenv('DOCUMENT_ID')

    if document_id:
        debug_flag = '--debug' in sys.argv
        main(document_id, debug_flag)
    else:
        logger.error("No document ID provided.")

# Tools for LangChain agent
tools = [
    Tool(
        name="PDF OCR",
        description="Extract text from a PDF document using OCR",
        func=LocalFileToolsOCR().run,
    ),
    Tool(
        name="Summarize",
        description="Summarize the content of a document",
        func=LocalFileToolsSummarize().run,
    ),
    Tool(
        name="Read File",
        description="Read and return the content of a local file",
        func=LocalFileURLReader().run,
    ),
]

# Define an agent using the configured tools and LLM
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    max_iterations=3,
)

# Example agent usage
pdf_path = "/path/to/your/pdf_file.pdf"
with open(pdf_path, "rb") as f:
    pdf_content = f.read()

# Load the PDF document
loader = PyMuPDFLoader(pdf_content)
documents = loader.load()

# Split the documents into smaller chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.split_documents(documents)

# Create a Chroma vector store
db = Chroma.from_documents(texts, embeddings)

# Create a chain to answer questions based on the vector store
qa = VectorDBQAWithSourcesChain.from_chain_type(
    llm=llm,
    chain_type="stuff",
    vectorstore_factory=db.as_retriever(),
    return_source_documents=True,
)

# Ask a question
query = "What is the main topic of this document?"
result = qa({"query": query})
print(f"Answer: {result['result']}")

# Use the agent for more complex tasks
agent_input = (
    "I need help understanding and summarizing the key information in this PDF document. "
    "Can you please extract the main points, dates, names, and any other relevant details?"
)
agent_result = agent.run(agent_input)
print(f"Agent Result: {agent_result}")
