# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Shows how to generate text with Meta Llama 2 Chat (on demand).
"""

import json
import logging
import boto3


from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def generate_text(model_id, body):
    """
    Generate an image using Meta Llama 2 Chat on demand.
    Args:
        model_id (str): The model ID to use.
        body (str) : The request body to use.
    Returns:
        response (JSON): The text that the model generated, token information, and the
        reason the model stopped generating text.
    """

    logger.info("Generating image with Meta Llama 2 Chat model %s", model_id)

    bedrock = boto3.client(service_name='bedrock-runtime')

    accept = "application/json"
    content_type = "application/json"

    response = bedrock.invoke_model(
        body=body, modelId=model_id, accept=accept, contentType=content_type
    )

    response_body = json.loads(response.get('body').read())

    return response_body


def main():
    """
    Entrypoint for Meta Llama 2 Chat example.
    """

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s: %(message)s")

    model_id = 'meta.llama2-13b-chat-v1'
    prompt = """What is the average lifespan of a Llama?"""
    max_gen_len = 128
    temperature = 0.1
    top_p = 0.9


    # Create request body.
    body = json.dumps(
        {
            "model": "anthropic.claude-3-sonnet-20240229-v1:0",
            "max_tokens": 1024,
            "tools": [{
                "name": "get_weather",
                "description": "Get the current weather in a given location",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "The unit of temperature, either \"celsius\" or \"fahrenheit\""
                        }
                    },
                    "required": ["location"]
                }
            }],
            "messages": [{"role": "user", "content": "What is the weather like in San Francisco?"}]
        }
    )


    try:

        response = generate_text(model_id, body)

        print(f"Generated Text: {response['generation']}")
        print(f"Prompt Token count:  {response['prompt_token_count']}")
        print(f"Generation Token count:  {response['generation_token_count']}")
        print(f"Stop reason:  {response['stop_reason']}")

    except ClientError as err:
        message = err.response["Error"]["Message"]
        logger.error("A client error occurred: %s", message)
        print("A client error occured: " +
              format(message))

    else:
        print(
            f"Finished generating text with Meta Llama 2 Chat model {model_id}.")


if __name__ == "__main__":
    main()

