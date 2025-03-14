import time
import keyboard
from agent.llm_utils.omniparserclient import OmniParserClient
from executor.anthropic_executor import AnthropicExecutor

# Define supported models from OpenRouter.
SUPPORTED_MODELS = [
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "qwen/qwen2.5-vl-72b-instruct:free",
    "google/gemini-2.0-flash-thinking-exp:free",
    "google/gemini-exp-1206:free",
    "meta-llama/llama-3.2-11b-vision-instruct:free"
]

def check_killswitch():
    if keyboard.is_pressed('F2'):
        time.sleep(0.2)
        if keyboard.is_pressed('F2'):
            return True
    return False

def sampling_loop_sync(*, model, provider, messages, output_callback, tool_output_callback, api_response_callback, api_key, only_n_most_recent_images=2, max_tokens=4096, omniparser_url, state):
    print('Starting sampling loop with model:', model)
    omniparser_client = OmniParserClient(url=f"http://{omniparser_url}/parse/")
    if model in SUPPORTED_MODELS:
        from agent.openrouter_agent import OpenRouterAgent
        actor = OpenRouterAgent(
            model=model,
            api_key=api_key,
            max_tokens=max_tokens,
            output_callback=output_callback,
            only_n_most_recent_images=only_n_most_recent_images
        )
        executor = AnthropicExecutor(output_callback=output_callback, tool_output_callback=tool_output_callback)
        while True:
            if check_killswitch():
                print("Killswitch activated. Exiting loop.")
                break
            if state.get("stop", False):
                print("Stop flag set. Exiting loop.")
                break
            parsed_screen = omniparser_client()
            state["parsed_screen"] = parsed_screen
            screen_context = "Screen Info:\n" + parsed_screen.get("screen_info", "")
            if "original_screenshot_base64" in parsed_screen:
                screen_context += "\n[Raw screenshot attached]"
            messages.append({"role": "user", "content": [screen_context]})
            assistant_msg = actor(messages=messages, parsed_screen=parsed_screen)
            for message, tool_result in executor(assistant_msg, messages, state):
                yield message
            if "Next Action: None" in assistant_msg.get("content", ""):
                break
            messages.append({"role": "user", "content": [f"Agent response: {assistant_msg}"]})
            time.sleep(1)
    else:
        print("Model not supported in this loop branch.")
    return messages
