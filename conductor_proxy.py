import logging
import json
import openai
import time
import uuid
from mitmproxy import http
from tiktoken import get_encoding
import tkinter as tk
from tkinter import messagebox
import requests

# mitmdump -s conductor_proxy.py -p 8080

# Configure logging
logging.basicConfig(filename='openai_proxy_combined.log', level=logging.INFO)

# Set your OpenAI API key
openai.api_key = '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'

# User-defined variables
LOCAL_LLM_HOST = "192.168.1.254" #localhost address (LM Studio, Ollama, llama.cpp, etc)
LOCAL_LLM_PORT = 2345 #localhost port
MAX_TOKEN_COUNT = 8192 #Threshold to swtich the model to OpenAI API; set this based on your LLM's context capability
MIDDLE_MAN_JSON = 'history.json'
OUTPUT_LOG = 'output.log'
OPENAI_OUTPUT_LOG = 'openai_output.log'

# Get the encoding for the "llama2" model
encoding = get_encoding("cl100k_base")

def process_request(request_data):
    messages = request_data['messages']
    completion = client.chat.completions.create(
        model="gpt-4-0125-preview",
        temperature=0.7,
        messages=messages,
    )
    response_text = completion.choices[0].message.content.strip()
    return response_text

def write_to_json(instruction, output, token_count, client, filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    data.append({
        "instruction": instruction,
        "output": output,
        "tokens": token_count,
        "client": client
    })
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Specify which model parameters to override for the local host
# These default settings work well with the "LoupGarou/deepseek-coder-6.7b-instruct-pythagora" model version 3
def modify_request_data(data):
    request_data = json.loads(data)
    request_data['model'] = "gpt-4-turbo-preview"
    request_data['temperature'] = 0.3
    request_data['n'] = 1
    request_data['top_p'] = 0.95
    request_data['top_k'] = 40
    request_data['presence_penalty'] = 0
    request_data['frequency_penalty'] = 0
    request_data['min_p'] = 0.05
    return json.dumps(request_data)

def request(flow: http.HTTPFlow) -> None:
    if flow.request.url.startswith("http://localhost:8080/v1/chat/completions"):
        request_data = json.loads(flow.request.text)
        messages = request_data['messages']

        # Modifier to apply to the token count (just a lazy fudge factor to guestimate DeepSeek-Coder tokens)
        modifier = 1.35

        # Calculate the token count
        token_count = 0
        for message in messages:
            role = message['role']
            content = message['content']
            token_count += len(encoding.encode(role))
            token_count += len(encoding.encode(content))

        # Add the token count for the system prompt
        system_prompt = "Your system prompt goes here"
        token_count += len(encoding.encode(system_prompt))

        # Apply the modifier to the token count
        token_count = int(token_count * modifier)

        # Initialize an empty list to hold content messages
        content_messages = []

        # Log the input messages and collect content for JSON writing
        for message in messages:
            role = message['role']
            content = message['content']
            if content:  # Only process messages with non-empty content
                logging.info(f"{role.capitalize()} Input: {content}")
                content_messages.append(content)  # Only append the content

        # Join the content messages to construct a single instruction string
        instruction = ' '.join(content_messages)

        if token_count >= MAX_TOKEN_COUNT:
            # OpenAPI process
            response_text = process_request(request_data)

            # Log the output
            logging.info(f"Output: {response_text}")

            response_data = {
                "choices": [
                    {
                        "delta": {
                            "content": response_text
                        },
                        "index": 0,
                        "finish_reason": "stop"
                    }
                ],
                "created": int(time.time()),
                "id": str(uuid.uuid4()),
                "model": "gpt-4",
                "object": "chat.completion.chunk"
            }

            flow.request.url = "https://api.openai.com/v1/chat/completions"
            flow.request.host = "api.openai.com"
            flow.request.port = 443
            flow.request.scheme = "https"

            flow.response = http.Response.make(
                200,
                json.dumps(response_data),
                {"Content-Type": "application/json"}
            )

            # Write input and output to JSON file
            write_to_json(instruction, response_text, token_count, "OpenAI", MIDDLE_MAN_JSON)
        else:
            # Modify the request data
            modified_data = modify_request_data(flow.request.text)

            flow.request.text = modified_data
            flow.request.host = LOCAL_LLM_HOST
            flow.request.port = LOCAL_LLM_PORT

            logging.info(f"Modified Request: {flow.request.text}")

# Configure logging for capturing output sent back to the program
output_logging = logging.getLogger('output_logger')
output_logging.setLevel(logging.INFO)
output_handler = logging.FileHandler(OUTPUT_LOG)
output_handler.setFormatter(logging.Formatter('%(message)s'))
output_logging.addHandler(output_handler)

openai_output_logging = logging.getLogger('openai_output_logger')
openai_output_logging.setLevel(logging.INFO)
openai_output_handler = logging.FileHandler(OPENAI_OUTPUT_LOG)
openai_output_handler.setFormatter(logging.Formatter('%(message)s'))
openai_output_logging.addHandler(openai_output_handler)

def response(flow: http.HTTPFlow) -> None:
    if flow.request.url.startswith("https://api.openai.com/v1/chat/completions"):
        logging.info(f"Response: {flow.response.text}")
        
        # Log the exact OpenAI output being sent back to the program
        openai_output_logging.info(flow.response.text)
        
    elif flow.request.url.startswith(f"http://{LOCAL_LLM_HOST}:{LOCAL_LLM_PORT}/v1/chat/completions"):
        logging.info(f"Response: {flow.response.text}")
        
        # Write input and output to JSON file for requests under MAX_TOKEN_COUNT tokens
        request_data = json.loads(flow.request.text)
        messages = request_data['messages']
        
        # Initialize an empty list to hold content messages
        content_messages = []
        
        # Collect content for JSON writing
        for message in messages:
            role = message['role']
            content = message['content']
            content_messages.append(content)
        
        # Join the content messages to construct a single instruction string
        instruction = ' '.join(content_messages)
        
        # Store the original request data
        original_request_data = json.loads(flow.request.text)
        
        while True:
            # Parse the SSE output and extract the content
            response_text = ""
            for line in flow.response.text.strip().split("\n"):
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data != "[DONE]":
                        chunk = json.loads(data)
                        if "delta" in chunk["choices"][0] and "content" in chunk["choices"][0]["delta"]:
                            content = chunk["choices"][0]["delta"]["content"]
                            response_text += content
            
            break
        
        # Calculate the token count
        token_count = 0
        for message in messages:
            role = message['role']
            content = message['content']
            token_count += len(encoding.encode(role))
            token_count += len(encoding.encode(content))

        # Add system prompt to token count
        system_prompt = "You are an AI programming assistant, utilizing the DeepSeek Coder model, developed by DeepSeek Company, and you only answer questions related to computer science. For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer."
        token_count += len(encoding.encode(system_prompt))
        
        # Apply the modifier to the token count
        token_count = int(token_count * 1.35)
        
        # Write input and output to JSON file
        write_to_json(instruction, response_text, token_count, "Local LLM", MIDDLE_MAN_JSON)
        
        # Log the SSE output
        output_logging.info(flow.response.text)
        
        # Log the extracted response text
        output_logging.info(f"Extracted Response: {response_text}")
