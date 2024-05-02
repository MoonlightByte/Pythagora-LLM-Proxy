# Pythagora LLM Proxy

This project acts as a proxy between the [Pythagora GPT Pilot](https://github.com/Pythagora-io/gpt-pilot) and a local host, such as [LM Studio](https://lmstudio.ai), allowing GPT Pilot to utilize Large Language Models (LLMs) without needing to use the [OpenAI API](https://openai.com/). The code formats the OpenAI API prompt into an instruction and output prompt compatible with the [DeepSeek-Coder instruct code base](https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct).

## Model Compatibility

Both [DeepSeek-Coder instruct 6.7b model](https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct) and [DeepSeek-Coder instruct 33b model](https://huggingface.co/deepseek-ai/deepseek-coder-33b-instruct) have been fine-tuned for compatibility with the GPT Pilot application. The fine-tuned models can be found at [LoupGarou/deepseek-coder-6.7b-instruct-pythagora-v2-gguf](https://huggingface.co/LoupGarou/deepseek-coder-6.7b-instruct-pythagora-v2-gguf) and [LoupGarou/deepseek-coder-33b-instruct-pythagora-gguf](https://huggingface.co/LoupGarou/deepseek-coder-33b-instruct-pythagora-gguf).

## Known Issues & Error Handling

These 6.7b and 33b models work best when used with the accompanying proxy script from GitHub: [Pythagora-LLM-Proxy](https://github.com/MoonlightByte/Pythagora-LLM-Proxy). I recommend you use the latest Pythagora LLM Proxy to ensure proper error handling and formatting.

<u><b>Please use version 2 of the 6.7b model now available at [LoupGarou/deepseek-coder-6.7b-instruct-pythagora-v2-gguf](https://huggingface.co/LoupGarou/deepseek-coder-6.7b-instruct-pythagora-v2-gguf)</b></u>

Here's current list of error handling to address known issues with version 1:

1. **Re-query missing plans**: Occasionally, the model may not produce a plan and instead pass `"plan": []` which causes Pythagora to report 100% complete.

2. **Re-query missing tasks**: Under certain circumstances, the model may not generate tasks when necessary and instead pass `"tasks": []` which may cause issues with application development.

3. **Re-query repetitive questions**: During the initial planning stage, when the project description is short, the model may repeat the same questions and get stuck in a loop.

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/MoonlightByte/Pythagora-LLM-Proxy.git
   cd Pythagora-LLM-Proxy
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up the environment variables in the `.env` file:
   - `LOCAL_LLM_HOST`: The localhost address for the LLM (e.g., LM Studio, Ollama, llama.cpp, etc.).
   - `LOCAL_LLM_PORT`: The localhost port for the LLM.
   - `MAX_TOKEN_COUNT`: The threshold to switch the model to the OpenAI API. Set this based on your LLM's context capability.
   - `MIDDLE_MAN_JSON`: The filename for storing the conversation history (default: `history.json`).
   - `OUTPUT_LOG`: The filename for logging the output (default: `output.log`).
   - `OPENAI_OUTPUT_LOG`: The filename for logging the OpenAI output (default: `openai_output.log`).

4. Start the proxy:
   ```
   mitmdump -s conductor_proxy.py -p 8080
   ```

5. Configure GPT Pilot to use the proxy by setting the OpenAI API endpoint to `http://localhost:8080/v1/chat/completions`. For example, comment out your OpenAI API values and append your Pythagora .env files as follows:
   ```
   #Deepseek-Coder
   OPENAI_ENDPOINT=http://localhost:8080/v1/chat/completions
   OPENAI_API_KEY=:"not-needed"
   ```

## Usage

The proxy will intercept the API requests from GPT Pilot and format them into an instruction and output prompt compatible with the DeepSeek-Coder instruct model. If the token count exceeds the specified `MAX_TOKEN_COUNT`, the request will be sent to the OpenAI API instead. This is useful in circumstances where the token count needed by Pythagora exceeds the capabilities of the local model.

The conversation history and output logs will be stored in the specified files (`MIDDLE_MAN_JSON`, `OUTPUT_LOG`, `OPENAI_OUTPUT_LOG`).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

The usage of the DeepSeek-Coder model is subject to the [DeepSeek-Coder Model License](https://github.com/deepseek-ai/deepseek-coder/blob/main/LICENSE-MODEL).

GPT Pilot is licensed under the MIT License. See the [GPT Pilot License](https://github.com/Pythagora-io/gpt-pilot/blob/main/LICENSE) for more information.

## Acknowledgements

- [Pythagora GPT Pilot](https://github.com/Pythagora-io/pythagora)
- [DeepSeek-Coder](https://github.com/deepseek-ai/deepseek-coder)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
