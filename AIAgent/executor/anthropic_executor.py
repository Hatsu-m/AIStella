"""
Executor for processing the agent's tool-use instructions.
It extracts the "Next Action" and, if provided, "Box ID" from the assistant's response.
If a Box ID is provided, it looks up the corresponding bounding box from the OmniParser output stored in state,
computes the centroid (converting normalized coordinates if needed),
and rewrites the tool command to include click coordinates.
Then it calls the ComputerTool (via ToolCollection) to execute the action.
It returns a message with the tool execution result.
"""

import asyncio
from tools.tool_collection import ToolCollection
from tools.computer import ComputerTool

import base64
from PIL import Image, ImageDraw
import io
import pyautogui

class AnthropicExecutor:
    def __init__(self, output_callback, tool_output_callback):
        self.tool_collection = ToolCollection(ComputerTool())
        self.output_callback = output_callback
        self.tool_output_callback = tool_output_callback

    def __call__(self, response, messages, state=None):
        if response not in messages:
            messages.append(response)

        content = response.get("content", "")
        next_action = "None"
        box_id = None

        # Parse Next Action and Box ID from the assistant response.
        try:
            lines = content.split("\n")
            for line in lines:
                if line.strip().startswith("Next Action:"):
                    next_action = line.strip()[len("Next Action:"):].strip()
                if line.strip().startswith("Box ID:"):
                    try:
                        box_id = int(line.strip()[len("Box ID:"):].strip())
                    except Exception:
                        box_id = None
        except Exception:
            next_action = "None"

        # Process the Box ID if provided and if OmniParser output exists.
        if box_id is not None and state is not None:
            parsed_screen = state.get("parsed_screen")
            if parsed_screen is not None:
                elements = parsed_screen.get("parsed_content_list") or []
                if 0 <= box_id < len(elements):
                    element = elements[box_id]
                    if element is None or not isinstance(element, dict):
                        next_action = "None"
                        state["debug_info"] = "Selected element is missing or invalid."
                    else:
                        bbox = element.get("bbox")
                        if bbox and isinstance(bbox, list) and len(bbox) == 4:
                            try:
                                # Convert all bbox values to floats.
                                bbox = [float(val) for val in bbox]
                            except Exception:
                                next_action = "None"
                                state["debug_info"] = "Bounding box values invalid."
                            else:
                                # If the bbox values are normalized (all <= 1), convert to pixels.
                                if max(bbox) <= 1:
                                    sw = parsed_screen.get("width")
                                    sh = parsed_screen.get("height")
                                    if sw is None or sh is None:
                                        next_action = "None"
                                        state["debug_info"] = "Screenshot dimensions missing."
                                    else:
                                        x0 = int(bbox[0] * sw)
                                        y0 = int(bbox[1] * sh)
                                        x2 = int(bbox[2] * sw)
                                        y2 = int(bbox[3] * sh)
                                else:
                                    # Assume bbox is already in pixels.
                                    x0, y0, x2, y2 = map(int, bbox)
                                
                                # Compute the center.
                                x_center = (x0 + x2) // 2
                                y_center = (y0 + y2) // 2

                                next_action = f"left_click({x_center},{y_center})"

                                selected_name = element.get("content", "N/A")
                                state["debug_info"] = (
                                    f"Raw bbox: {bbox}, Converted bbox: {[x0, y0, x2, y2]}, "
                                    f"Center: ({x_center},{y_center}), Selected Box ID: {box_id}, Name: {selected_name}"
                                )

                                # Update preview image: draw rectangle and label.
                                screenshot_b64 = parsed_screen.get("original_screenshot_base64", "")
                                if screenshot_b64:
                                    image_data = base64.b64decode(screenshot_b64)
                                    image = Image.open(io.BytesIO(image_data))
                                    draw = ImageDraw.Draw(image)
                                    draw.rectangle([x0, y0, x2, y2], outline="red", width=3)
                                    label_position = (x0, max(y0-15, 0))
                                    draw.text(label_position, f"Box {box_id}", fill="red")
                                    state["preview_image"] = image
                        else:
                            next_action = "None"
                            state["debug_info"] = "Bounding box missing or invalid."
                else:
                    next_action = "None"
                    state["debug_info"] = "Invalid Box ID"
                    screenshot_b64 = parsed_screen.get("original_screenshot_base64", "")
                    if screenshot_b64:
                        image_data = base64.b64decode(screenshot_b64)
                        image = Image.open(io.BytesIO(image_data))
                        draw = ImageDraw.Draw(image)
                        draw.text((10, 10), "Invalid Box ID", fill="red")
                        state["preview_image"] = image
            else:
                next_action = "None"
                state["debug_info"] = "No OmniParser output"

        # Execute the determined action only if valid.
        tool_result = None
        if next_action.lower() != "none" and next_action != "":
            try:
                tool_result = asyncio.run(
                    self.tool_collection.run(name="computer", tool_input={"action": next_action})
                )
                self.tool_output_callback(tool_result, "tool_" + str(id(tool_result)))
            except Exception as ex:
                tool_result = type("ToolResult", (), {})()
                tool_result.output = f"Error executing command: {str(ex)}"

        tool_message = {
            "role": "assistant",
            "content": (
                f"Tool executed: {tool_result.output}"
                if tool_result and hasattr(tool_result, "output") and tool_result.output
                else "No tool action executed."
            )
        }
        messages.append(tool_message)
        yield tool_message, tool_result
