"""
Agent that uses the OpenRouter API (with various supported vision–language models)
to determine the next PC control action.

It sends both the OmniParser output (text describing the UI elements and bounding boxes)
and the raw screenshot (base64-encoded PNG) to the LLM so it can leverage its vision.
Your response must be ONLY a valid JSON object with exactly the following keys:
  "Reasoning": A clear, concise explanation of what you see and how you plan to achieve the task.
  "Next Action": A single action command (from the allowed list) or "None".
  "Box ID": (only if the action is left_click, right_click, or double_click) the numeric identifier of the target element.
  "value": (only if the action is type) the text to type.
  
Allowed "Next Action" options:
- type: types a string of text.
- left_click: moves the mouse to the element with the specified Box ID and left-clicks.
- right_click: moves the mouse to the element with the specified Box ID and right-clicks.
- double_click: moves the mouse to the element with the specified Box ID and double-clicks.
- hover: moves the mouse to the element with the specified Box ID.
- scroll_up: scrolls up to reveal previous content.
- scroll_down: scrolls down to reveal additional content.
- wait: waits 1 second for the device to respond.

Example output:
{"Reasoning": "The screen shows a search bar with the query 'local pears'. I will click it to focus.", "Next Action": "left_click", "Box ID": 5}

IMPORTANT: Output ONLY the JSON object with no additional text.
"""

import json
import re
from datetime import datetime
from agent.llm_utils.openrouter_client import run_openrouter_interleaved

class OpenRouterAgent:
    def __init__(self, model, api_key, max_tokens, output_callback, only_n_most_recent_images):
        self.model = model
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.output_callback = output_callback
        self.only_n_most_recent_images = only_n_most_recent_images
        self.system = (
            f"<SYSTEM_CAPABILITY>\n"
            f"* You are using a Windows device with internet access.\n"
            f"* The current date is {datetime.today().strftime('%A, %B %d, %Y')}.\n"
            f"</SYSTEM_CAPABILITY>\n\n"
            "You are an AI agent controlling a Windows PC. You interact only with the desktop GUI using a mouse and keyboard. \n\n"
            "You will be provided with two pieces of information:\n"
            "1. Textual details from OmniParser describing UI elements and detected bounding boxes.\n"
            "2. A raw screenshot of the current screen (base64 encoded image).\n\n"
            "Focus on the main screen elements and ignore extraneous background information. \n\n"
            "Based on this combined context, decide the single next action to complete the task. "
            "Your available 'Next Action' options are:\n"
            "- type: types a string of text.\n"
            "- left_click: moves the mouse to the element with the specified Box ID and left-clicks.\n"
            "- right_click: moves the mouse to the element with the specified Box ID and right-clicks.\n"
            "- double_click: moves the mouse to the element with the specified Box ID and double-clicks.\n"
            "- hover: moves the mouse to the element with the specified Box ID.\n"
            "- scroll_up: scrolls up to reveal previous content.\n"
            "- scroll_down: scrolls down to reveal additional content.\n"
            "- wait: waits 1 second for the device to load or respond.\n\n"
            "Based on the provided visual and textual context, output a valid JSON object with exactly "
            "the following keys (and no others):\n"
            "- \"Reasoning\": your explanation and step-by-step analysis of what to do next.\n"
            "- \"Next Action\": one of the allowed actions (or \"None\" if no action is applicable).\n"
            "- \"Box ID\": (only if the action is left_click, right_click, or double_click) the numeric ID of the target element.\n"
            "- \"value\": (only if the action is type) the text to be typed.\n\n"
            "For actions that do not require a Box ID or value, do not include those keys.\n\n"
            "Example:\n"
            "{\"Reasoning\": \"The screen shows a search bar with the query 'local pears'. I will click it to focus.\", \"Next Action\": \"left_click\", \"Box ID\": 5}\n\n"
            "DO NOT add any extra text. Output MUST be ONLY the JSON object."
        )

    def __call__(self, messages, parsed_screen):
        try:
            screen_text = "Screen Info:\n" + parsed_screen.get("screen_info", "")
            text_block = {"type": "text", "text": screen_text}
            screenshot_b64 = parsed_screen.get("original_screenshot_base64", "")
            image_block = None
            if screenshot_b64:
                image_block = {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
            directive_block = {"type": "text", "text": "DO NOT add extra text. Output must be ONLY JSON."}
            content_list = [text_block, directive_block]
            if image_block:
                content_list.append(image_block)
            messages.append({"role": "user", "content": content_list})
            
            print("DEBUG: Message payload to LLM (without image):", {"role": "user", "content": [text_block, directive_block]})
            
            response_text, token_usage = run_openrouter_interleaved(
                messages=messages,
                system=self.system,
                model_name=self.model,
                api_key=self.api_key,
                max_tokens=self.max_tokens,
                temperature=0
            )
            print("DEBUG: Raw response from LLM:", response_text)
            
            start_index = response_text.find("{")
            end_index = response_text.rfind("}")
            if start_index != -1 and end_index != -1 and end_index > start_index:
                json_candidate = response_text[start_index:end_index+1].strip()
            else:
                json_candidate = response_text.strip()
            
            response_json = json.loads(json_candidate)
            if "Reasoning" not in response_json:
                response_json["Reasoning"] = ""
            if "Next Action" not in response_json:
                response_json["Next Action"] = "None"
            
            assistant_content = f"Reasoning: {response_json['Reasoning']}\nNext Action: {response_json['Next Action']}"
            if "Box ID" in response_json:
                assistant_content += f"\nBox ID: {response_json['Box ID']}"
            if "value" in response_json:
                assistant_content += f"\nvalue: {response_json['value']}"
            
            assistant_msg = {
                "role": "assistant",
                "content": assistant_content
            }
            print("DEBUG: Agent output:", assistant_msg)
            return assistant_msg
        except Exception as ex:
            fallback_msg = {
                "role": "assistant",
                "content": f"Reasoning: Agent error: {str(ex)}\nNext Action: None"
            }
            print("DEBUG: Agent error:", fallback_msg)
            return fallback_msg
