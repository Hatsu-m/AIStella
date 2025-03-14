"""
Run the OmniTool application using OpenRouter API.
This app uses the OmniParser server (assumed running at the specified URL)
to process screenshots and then uses our OpenRouter-based agent for PC control.
Run with:
    python app.py --windows_host_url localhost:8006 --omniparser_server_url localhost:8000 --server_port 7889
"""

import os
from datetime import datetime
from enum import StrEnum
from pathlib import Path
import argparse
import gradio as gr
import requests
import base64

# Configuration directory for saving API keys (if needed)
CONFIG_DIR = Path("~/.anthropic").expanduser()

INTRO_TEXT = '''
OmniTool lets you turn any vision–language model into an AI agent.
Supported models:
• google/gemini-2.0-flash-lite-preview-02-05:free  
• qwen/qwen2.5-vl-72b-instruct:free  
• google/gemini-2.0-flash-thinking-exp:free  
• google/gemini-exp-1206:free  
• meta-llama/llama-3.2-11b-vision-instruct:free  
Type a command and press Send to start.
Press the Stop button or press F2 twice (killswitch) to halt actions.
'''

def parse_arguments():
    parser = argparse.ArgumentParser(description="Gradio App for OmniTool with OpenRouter")
    parser.add_argument("--windows_host_url", type=str, default='localhost:8006')
    parser.add_argument("--omniparser_server_url", type=str, default="localhost:8000")
    parser.add_argument("--server_port", type=int, default=7888, help="Server port for Gradio interface")
    return parser.parse_args()

args = parse_arguments()

class Sender(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

def setup_state(state):
    if "messages" not in state:
        state["messages"] = []  # conversation history for agent
    if "chatbot_messages" not in state:
        state["chatbot_messages"] = []  # for UI display
    if "model" not in state:
        state["model"] = "meta-llama/llama-3.2-11b-vision-instruct:free"  # default model
    if "provider" not in state:
        state["provider"] = "openrouter"
    if "api_key" not in state:
        state["api_key"] = os.getenv("OPENROUTER_API_KEY", "")
    if "only_n_most_recent_images" not in state:
        state["only_n_most_recent_images"] = 2
    if "stop" not in state:
        state["stop"] = False
    if "preview_image" not in state:
        state["preview_image"] = None
    if "debug_info" not in state:
        state["debug_info"] = ""

async def main(state):
    setup_state(state)
    return "Setup completed"

def chatbot_output_callback(message, sender="assistant"):
    print(f"[{sender}]: {message}")

def _stop_app(state):
    state["stop"] = True
    return None

def clear_chat(state):
    state["messages"] = []
    state["chatbot_messages"] = []
    # Also clear the preview image and debug info
    state["preview_image"] = None
    state["debug_info"] = ""
    return state["chatbot_messages"]

def update_model(model_val, state):
    state["model"] = model_val
    return gr.update()

def process_input(user_input, state):
    if state["stop"]:
        state["stop"] = False
    if not state["api_key"].strip():
        raise gr.Error("API Key is not set")
    if not user_input:
        raise gr.Error("No command provided")
    
    user_msg = {"role": "user", "content": user_input}
    state["messages"].append(user_msg)
    state["chatbot_messages"].append(user_msg)
    yield state["chatbot_messages"], state.get("preview_image"), state.get("debug_info", "")
    
    from loop import sampling_loop_sync
    for loop_msg in sampling_loop_sync(
        model=state["model"],
        provider=state["provider"],
        messages=state["messages"],
        output_callback=chatbot_output_callback,
        tool_output_callback=lambda tool_output, tool_id: None,
        api_response_callback=lambda response: None,
        api_key=state["api_key"],
        only_n_most_recent_images=state["only_n_most_recent_images"],
        max_tokens=16384,
        omniparser_url=args.omniparser_server_url,
        state=state
    ):
        state["chatbot_messages"].append(loop_msg)
        yield state["chatbot_messages"], state.get("preview_image"), state.get("debug_info", "")

def get_header_image_base64():
    try:
        script_dir = Path(__file__).parent
        image_path = script_dir.parent.parent / "imgs" / "header_bar_thin.png"
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            return f'data:image/png;base64,{encoded_string}'
    except Exception as e:
        print(f"Failed to load header image: {e}")
        return None

with gr.Blocks(theme=gr.themes.Default()) as demo:
    gr.HTML("""
        <style>
        .no-padding { padding: 0 !important; }
        .markdown-text p { font-size: 18px; }
        </style>
    """)
    state = gr.State({})
    setup_state(state.value)
    
    gr.HTML('<h1 style="text-align: center; font-weight: normal;">Omni<span style="font-weight: bold;">Tool</span></h1>')
    gr.Markdown(INTRO_TEXT, elem_classes="markdown-text")
    
    with gr.Accordion("Settings", open=True):
        with gr.Row():
            with gr.Column():
                model_dropdown = gr.Dropdown(
                    label="Vision–Language Model",
                    choices=[
                        "google/gemini-2.0-flash-lite-preview-02-05:free",
                        "qwen/qwen2.5-vl-72b-instruct:free",
                        "google/gemini-2.0-flash-thinking-exp:free",
                        "google/gemini-exp-1206:free",
                        "meta-llama/llama-3.2-11b-vision-instruct:free"
                    ],
                    value="meta-llama/llama-3.2-11b-vision-instruct:free",
                    interactive=True,
                )
            with gr.Column():
                only_n_images = gr.Slider(
                    label="N most recent screenshots",
                    minimum=0,
                    maximum=10,
                    step=1,
                    value=2,
                    interactive=True
                )
        with gr.Row():
            with gr.Column():
                api_key = gr.Textbox(
                    label="OpenRouter API Key",
                    type="password",
                    placeholder="Paste your OpenRouter API key here",
                    interactive=True,
                    value=state.value.get("api_key", "")
                )
    
    with gr.Row():
        with gr.Column(scale=8):
            chatbot = gr.Chatbot(label="Chat History", height=580, type="messages")
        with gr.Column(scale=3):
            gr.Markdown("**Local PC Control Active**", elem_classes="markdown-text")
            # Live feed preview image (PIL image)
            preview_image = gr.Image(label="OmniParser Preview", interactive=False, type="pil")
            # Debug info text field (read-only)
            debug_info = gr.Textbox(label="Debug Info", interactive=False)
    
    with gr.Row():
        chat_input = gr.Textbox(show_label=False, placeholder="Type a command to control your PC...", container=False)
    with gr.Row():
        submit_button = gr.Button(value="Send", variant="primary")
        stop_button = gr.Button(value="Stop", variant="secondary")
        clear_button = gr.Button("Clear Chat", variant="secondary")
    
    model_dropdown.change(fn=update_model, inputs=[model_dropdown, state])
    only_n_images.change(
        fn=lambda val, st: st.update({"only_n_most_recent_images": val}) or val,
        inputs=[only_n_images, state], outputs=state
    )
    api_key.change(
        fn=lambda val, st: st.update({"api_key": val}) or val,
        inputs=[api_key, state], outputs=api_key
    )
    
    clear_button.click(fn=clear_chat, inputs=[state], outputs=[chatbot])
    submit_button.click(fn=process_input, inputs=[chat_input, state], outputs=[chatbot, preview_image, debug_info])
    stop_button.click(fn=_stop_app, inputs=[state], outputs=None)
    
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=args.server_port)
