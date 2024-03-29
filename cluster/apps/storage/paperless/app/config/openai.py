#!/usr/bin/env python

import random
import time
from dateutil import parser
from datetime import datetime
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
OPENAI_API_ENDPOINT = "https://api.openai.com"

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def is_pdf_image_only(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            if page.get_text("text"):
                return False
        return True
    except Exception as e:
        logger.error(f"Error checking if PDF is image-only: {e}")
        return False

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
    url = f'{PAPERLESS_HOST}/documents/{document_id}/download/?original=true'
    logger.info(f"Downloading document from: {url}")
    headers = {"Authorization": f"Token {PAPERLESS_API_KEY}"}
    response = requests.get(url, headers=headers)
    logger.info(f"Status code: {response.status_code}")

    if response.status_code != 200:
        logger.error(f"Failed to download document. Status code: {response.status_code}")
        return None, None

    content_type = response.headers.get('Content-Type', '')
    return response.content, content_type


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

def ocr_document(image_path, debug=False):
    retry_wait = 5  # Initial backoff wait time in seconds
    max_retries = 8
    for attempt in range(max_retries):
        try:
          resized_image_path = resize_image(image_path)
          if not resized_image_path:
              return None

          base64_image = encode_image(resized_image_path)
          headers = {
              "Content-Type": "application/json",
              "Authorization": f"Bearer {OPENAI_API_KEY}"
          }
          payload = {
              "model": "gpt-4-vision-preview",
              "messages": [
                  {
                      "role": "user",
                      "content": [
                          {
                              "type": "text",
                              "text": "Only provide the OCR text from this image. Do not provide any additional commentary or text that is not in the image"
                          },
                          {
                              "type": "image_url",
                              "image_url": {
                                  "url": f"data:image/jpeg;base64,{base64_image}"
                              }
                          }
                      ]
                  }
              ],
              "max_tokens": 4096
          }
          if debug:
              debug_json = {'id': 'chatcmpl-95RcNLqoVk9gY6qaUZDddAZh8JdeK', 'object': 'chat.completion', 'created': 1711084831, 'model': 'gpt-4-1106-vision-preview', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': 'Lowes\nHow doers\nget more done.\n\n00001 66868 03/19/24 11:39 AM\nSALE CASHIER BRAD\n\n678885209193 BEHR CAULK <A>\nBEHR RAPID DRY CAULK 10.1 OZ WHITE\n$11.96\n\n079340689695 LOCPROFCON <A>\nLOCTITE ULTRA LIQ SUPER GLUE .14 OZ\n$10.36\n\n730232000126 12MMBIRCH <A>\n1/2 4X8 BIRCH PLYWOOD\n$69.58\n\nSUBTOTAL $91.90\nSALES TAX $9.42\nTOTAL $101.32\nCASH $102.00\nCHANGE DUE $0.68\n\n4706 03/19/24 11:39 AM\n4706 01 66868 03/19/2024 0770\n\nRETURN POLICY DEFINITIONS\nPOLICY ID DAYS POLICY EXPIRES ON\n1 90 06/17/2024\nA\n\nDID WE NAIL IT?\n\nTake a short survey for a chance to WIN\nA $5,000 LOWES GIFT CARD'}, 'finish_reason': 'length'}], 'usage': {'prompt_tokens': 1475, 'completion_tokens': 300, 'total_tokens': 1775}, 'system_fingerprint': None}
              return debug_json
          else:
              api_endpoint = f"{OPENAI_API_ENDPOINT}/v1/chat/completions"
              response = requests.post(api_endpoint, headers=headers, json=payload)
              if response.status_code == 200:
                  # Successful response
                  return response.json()
              elif response.status_code == 429:
                  # Rate limit exceeded, handle retry logic
                  retry_after = int(response.headers.get("Retry-After", retry_wait))
                  time_to_wait = max(retry_wait, retry_after)
                  logger.error(f"Rate limit exceeded. Retrying in {time_to_wait} seconds...")
                  time.sleep(time_to_wait)
                  retry_wait *= 2  # Exponential backoff
                  retry_wait += random.uniform(-0.5, 0.5) * retry_wait  # Add jitter
                  continue  # Continue with the next iteration of the loop
              else:
                  # Other HTTP errors
                  logger.error(f"OCR request failed with status code {response.status_code}: {response.text}")
                  return None
        except requests.exceptions.RequestException as e:
          # Handle non-HTTP errors (network issues, etc.)
          logger.error(f"Error during OCR request: {e}")
          return None

    # If all retries fail
    logger.error("Max retries exceeded for OCR document request")
    return None

def classify_document(image_path, ocr_text, tags, correspondents, document_types, debug=False):
    retry_wait = 5  # Initial backoff wait time in seconds
    max_retries = 8
    for attempt in range(max_retries):
        try:
          resized_image_path = resize_image(image_path)
          if not resized_image_path:
              return None

          base64_image = encode_image(resized_image_path)
          tags_str = ", ".join([f"'{tag['name']}'" for tag in tags])
          correspondents_str = ", ".join([f"'{correspondent['name']}'" for correspondent in correspondents])
          document_types_str = ", ".join([f"'{doc_type['name']}'" for doc_type in document_types])

          base_prompt = "Based on the image content and the OCR text provided, determine the date the document was created, most appropriate correspondent, and document type. From the provided list, select all tags that apply. Only use the options provided; if nothing matches, leave it blank. Also add a short description to be used as the document title."

          prompt_text = (
              f"{base_prompt}\n\n"
              f"Tag options: {tags_str}\n\n"
              f"Correspondent options: {correspondents_str}\n\n"
              f"Document type options: {document_types_str}\n\n"
              "Provide the results in JSON format: {'creation_date': '', 'tag': [], 'correspondent': '', 'document_type': '', 'title': ''}"
          )

          headers = {
              "Content-Type": "application/json",
              "Authorization": f"Bearer {OPENAI_API_KEY}"
          }

          payload = {
              "model": "gpt-4-vision-preview",
              #"model": "gpt-4-0125-preview",
              "messages": [
                  {
                      "role": "user",
                      "content": [
                          {
                              "type": "text",
                              "text": ocr_text + "\n\n" + prompt_text
                          },
                          {
                              "type": "image_url",
                              "image_url": {
                                  "url": f"data:image/jpeg;base64,{base64_image}"
                              }
                          }
                      ]
                  }
              ],
              "max_tokens": 4096
          }

          try:
              api_endpoint = f"{OPENAI_API_ENDPOINT}/v1/chat/completions"
              response = requests.post(api_endpoint, headers=headers, json=payload)
              logger.info(f"Classification result: {response.json()}")
              if response.status_code == 200:
                  return response.json()
              else:
                  logger.error(f"Classification request failed with status code {response.status_code}: {response.text}")
                  return None
          except requests.exceptions.RequestException as e:
              logger.error(f"Error during classification request: {e}")
              return None
          pass

        except requests.exceptions.RequestException as e:
            if e.response and e.response.status_code == 429:
                # Extract the retry wait time from the error response if available
                retry_after = int(e.response.headers.get("Retry-After", retry_wait))
                # Use the server-provided value or exponentially increase the wait time
                time_to_wait = max(retry_wait, retry_after)
                print(f"Rate limit exceeded. Retrying in {time_to_wait} seconds...")
                time.sleep(time_to_wait)
                # Exponentially increase the wait time for the next attempt
                retry_wait *= 2
                # Add jitter by randomizing the wait time
                retry_wait = max(1, retry_wait + random.uniform(-0.5, 0.5) * retry_wait)
            else:
                # For other types of RequestExceptions, raise the exception
                raise
    else:
        # Raise an exception if all retries fail
        raise Exception("Max retries exceeded for Classify document request")


def extract_classification_data(classification_result):
    # Assuming classification_result is the JSON response from the classify_document function
    # Extracting the actual JSON string from the message content
    content = classification_result['choices'][0]['message']['content']
    json_str = content.split('```json')[1].split('```')[0].strip()
    return json.loads(json_str)


def update_document_content(document_id, ocr_text, classification_result, tags, correspondents, document_types):
    # Extract the classification data
    classification_data = extract_classification_data(classification_result)

    # Find the IDs for the tags, correspondent, and document type
    tag_ids = []
    for tag_name in classification_data['tag']:
        tag_id = next((tag['id'] for tag in tags if tag['name'] == tag_name), None)
        if tag_id:
            tag_ids.append(tag_id)

    correspondent_id = next((correspondent['id'] for correspondent in correspondents if correspondent['name'] == classification_data['correspondent']), None)
    document_type_id = next((doc_type['id'] for doc_type in document_types if doc_type['name'] == classification_data['document_type']), None)

    # Convert the creation date to the correct format using dateutil
    creation_date = classification_data.get('creation_date', '')
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
        "title": classification_data['title']
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

    file_content, content_type = download_document(document_id)
    if not file_content:
        logger.error("Failed to download document.")
        return

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(file_content)
        tmp_file_path = tmp_file.name

    # Initialize an empty list to collect OCR text from all pages
    aggregated_ocr_text = []

    # OCR the document if it is a PDF and contains only images
    if content_type == 'application/pdf' and is_pdf_image_only(tmp_file_path):
        logger.info("PDF contains only images, extracting for OCR...")
        with fitz.open(tmp_file_path) as doc:
            for page_number in range(len(doc)):
                page = doc.load_page(page_number)
                pix = page.get_pixmap()
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as img_file:
                    pix.save(img_file.name)
                    ocr_result = ocr_document(img_file.name, debug)
                    if ocr_result:
                        ocr_text = ocr_result['choices'][0]['message']['content']
                        aggregated_ocr_text.append(ocr_text)

                        # Perform classification only on the first page
                        if page_number == 0:
                            classification_result = classify_document(img_file.name, ocr_text, tags, correspondents, document_types, debug)

        # After all pages have been processed, update the document content with the aggregated OCR text
        if aggregated_ocr_text:
            full_ocr_text = "\n".join(aggregated_ocr_text)
            if classification_result:
                update_document_content(document_id, full_ocr_text, classification_result, tags, correspondents, document_types)


    # Handle image documents
    elif content_type in ['image/jpeg', 'image/png']:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(file_content)
            logger.info("Image file detected, processing with OCR...")
            ocr_result = ocr_document(tmp_file.name, debug)
            if ocr_result:
                ocr_text = ocr_result['choices'][0]['message']['content']
                classification_result = classify_document(tmp_file.name, ocr_text, tags, correspondents, document_types, debug)
                if classification_result:
                    # Process and update document content and metadata here
                    update_document_content(document_id, ocr_text, classification_result, tags, correspondents, document_types)

    logger.info("Run complete")


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
