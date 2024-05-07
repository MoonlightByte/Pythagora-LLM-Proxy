# Pythagora LLM Proxy

This project acts as a proxy between the [Pythagora GPT Pilot](https://github.com/Pythagora-io/gpt-pilot) and a local host, such as [LM Studio](https://lmstudio.ai), allowing GPT Pilot to utilize Large Language Models (LLMs) without needing to use the [OpenAI API](https://openai.com/). The code formats the OpenAI API prompt into an instruction and output prompt compatible with the [DeepSeek-Coder instruct code base](https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct).

Note: GPT Pilot will often generate instructions exceeding 10,000 tokens and occassionally exceeding 16,000 tokens which exceeds the capabilities of most LLMs. Therefore, consider this proxy as a way to offload work from OpenAI API to you local services and reduce the cost of development.

## Model Compatibility

Both [DeepSeek-Coder instruct 6.7b model](https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct) and [DeepSeek-Coder instruct 33b model](https://huggingface.co/deepseek-ai/deepseek-coder-33b-instruct) have been fine-tuned for compatibility with the GPT Pilot application. The fine-tuned models can be found at [LoupGarou/deepseek-coder-6.7b-instruct-pythagora-v3-gguf](https://huggingface.co/LoupGarou/deepseek-coder-6.7b-instruct-pythagora-v3-gguf) and [LoupGarou/deepseek-coder-33b-instruct-pythagora-gguf](https://huggingface.co/LoupGarou/deepseek-coder-33b-instruct-pythagora-gguf).

**Version 3:** [LoupGarou/deepseek-coder-6.7b-instruct-pythagora-v3-gguf](https://huggingface.co/LoupGarou/deepseek-coder-6.7b-instruct-pythagora-v3-gguf), is tested to be compatible with the following versions:

[GPT-Pilot (v.0.1.12)](https://github.com/Pythagora-io/gpt-pilot/tree/4c1ffa957742c47419ab1aba7f5bf62b3f00bb90) and 
[LM Studio (v.0.2.22)](https://releases.lmstudio.ai/windows/0.2.22/c/latest/LM-Studio-0.2.22-Setup.exe)

Please ensure you are using one of the above versions when working with this model to ensure proper functionality and compatibility.

## Optimal LLM Settings

To reduce empty plan, tasks, and circular questions, you must ensure three primary conditions are met:

1. **Prompt eval batch size (n_batch)**: LM Studio - Impacts how the instruction is divided and sent to the LLM. To prevent empty tasks, plans, and circular questions, set this to match your Context Length (n_ctx). For example, if your **n_ctx = 8192** then set your prompt eval bacth size to match **n_batch = 8192**. Warning: If the n_batch < n_ctx then your model will give bad results.
2. **Context Length (n_ctx)**: LM Studio - Sets the maximum length of the instruction and truncates the instruction once the limit is exceeded. Set this value to the maximum your hardware can handle and the maximum for the model. For example, DeepSeek Coder has a maximum token length of 16,384. Warning: GPT Pilot will often create instruction prompts 10,000 to 20,000 tokens in length which is why Pythagora-LLM-Proxy was created to permit toggling to higher capacity APIs such as OpenAI.
3. **System Prompt**: LM Studio - System Prompt must be set to DeepSeek Coder prompt: "You are an AI programming assistant, utilizing the DeepSeek Coder model, developed by DeepSeek Company, and you only answer questions related to computer science. For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer."
4. **MAX_TOKENS (GPT Pilot .env)**: GPT Pilot - Sets the maximum tokens the OpenAI API generate in the output. Warning: Setting this value too low will result in truncated messages.

## Known Issues & Error Handling

These 6.7b and 33b models work best when used with the accompanying proxy script from GitHub: [Pythagora-LLM-Proxy](https://github.com/MoonlightByte/Pythagora-LLM-Proxy). I recommend you use the latest Pythagora LLM Proxy to ensure proper error handling and formatting.

<u><b>Please use version 2 of the 6.7b model now available at [LoupGarou/deepseek-coder-6.7b-instruct-pythagora-v3-gguf](https://huggingface.co/LoupGarou/deepseek-coder-6.7b-instruct-pythagora-v3-gguf)</b></u>

<u><b>Version 2 of the 33b model is currently in training and will be ready soon after testing.</b></u>

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
