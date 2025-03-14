from openai import OpenAI
import os

def run_openrouter_interleaved(messages: list, system: str, model_name: str, api_key: str, max_tokens=256, temperature=0):
    client = OpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key=api_key,
    )
    
    extra_headers = {
        "HTTP-Referer": os.getenv("SITE_URL", "http://localhost"),
        "X-Title": os.getenv("SITE_NAME", "OmniTool")
    }
    
    payload_messages = [{"role": "system", "content": [{"type": "text", "text": system}]}]
    for m in messages:
        content_items = []
        for item in m.get("content", []):
            if isinstance(item, str):
                content_items.append({"type": "text", "text": item})
            elif isinstance(item, dict) and "type" in item:
                content_items.append(item)
            elif hasattr(item, "text"):
                content_items.append({"type": "text", "text": item.text})
            else:
                content_items.append({"type": "text", "text": str(item)})
        payload_messages.append({
            "role": m.get("role", "user"),
            "content": content_items
        })
    
    completion = client.chat.completions.create(
         extra_headers=extra_headers,
         model=model_name,
         messages=payload_messages,
         max_tokens=max_tokens,
         temperature=temperature,
    )
    
    text = completion.choices[0].message.content
    token_usage = completion.usage.total_tokens
    return text, token_usage
