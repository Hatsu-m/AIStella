import pyautogui
import time
import re
import asyncio
from tools.base import BaseAnthropicTool, ToolError, ToolResult

class ComputerTool(BaseAnthropicTool):
    name = "computer"
    
    def __init__(self, is_scaling: bool = False):
        super().__init__()
        self.is_scaling = is_scaling
    
    def execute_command(self, action: str) -> ToolResult:
        if not action:
            raise ToolError("No action provided")
        
        pattern = r"(\w+)(?:\((.*)\))?"
        match = re.match(pattern, action)
        if not match:
            raise ToolError(f"Action format not recognized: {action}")
        
        command = match.group(1)
        param = match.group(2)
        
        try:
            if command == "left_click":
                if param:
                    parts = param.split(",")
                    if len(parts) == 2:
                        x = int(parts[0].strip())
                        y = int(parts[1].strip())
                        # Adjust coordinates if in the top-left fail-safe region
                        if x < 10:
                            x = 10
                        if y < 10:
                            y = 10
                        pyautogui.click(x=x, y=y)
                        return ToolResult(output=f"Performed left click at ({x},{y})")
                    else:
                        raise ToolError("Invalid coordinates format for left_click")
                else:
                    pyautogui.click()
                    return ToolResult(output="Performed left click at current position")
            elif command == "right_click":
                if param:
                    parts = param.split(",")
                    if len(parts) == 2:
                        x = int(parts[0].strip())
                        y = int(parts[1].strip())
                        if x < 10:
                            x = 10
                        if y < 10:
                            y = 10
                        pyautogui.rightClick(x=x, y=y)
                        return ToolResult(output=f"Performed right click at ({x},{y})")
                    else:
                        raise ToolError("Invalid coordinates format for right_click")
                else:
                    pyautogui.rightClick()
                    return ToolResult(output="Performed right click at current position")
            elif command == "double_click":
                if param:
                    parts = param.split(",")
                    if len(parts) == 2:
                        x = int(parts[0].strip())
                        y = int(parts[1].strip())
                        if x < 10:
                            x = 10
                        if y < 10:
                            y = 10
                        pyautogui.doubleClick(x=x, y=y)
                        return ToolResult(output=f"Performed double click at ({x},{y})")
                    else:
                        raise ToolError("Invalid coordinates format for double_click")
                else:
                    pyautogui.doubleClick()
                    return ToolResult(output="Performed double click at current position")
            elif command == "hover":
                if param:
                    parts = param.split(",")
                    if len(parts) == 2:
                        x = int(parts[0].strip())
                        y = int(parts[1].strip())
                        if x < 10:
                            x = 10
                        if y < 10:
                            y = 10
                        pyautogui.moveTo(x, y, duration=0.25)
                        return ToolResult(output=f"Hovered at ({x},{y})")
                    else:
                        raise ToolError("Invalid coordinates format for hover")
                else:
                    pyautogui.moveRel(10, 0, duration=0.25)
                    return ToolResult(output="Performed hover (mouse moved slightly).")
            elif command == "type":
                if param is None:
                    raise ToolError("No text provided for type action")
                pyautogui.click()  # Focus input field
                pyautogui.write(param, interval=0.05)
                pyautogui.press('enter')
                return ToolResult(output=f"Typed: {param}")
            elif command == "scroll_up":
                pyautogui.scroll(100)
                return ToolResult(output="Scrolled up.")
            elif command == "scroll_down":
                pyautogui.scroll(-100)
                return ToolResult(output="Scrolled down.")
            elif command == "wait":
                time.sleep(1)
                return ToolResult(output="Waited for 1 second.")
            else:
                raise ToolError(f"Unknown command: {command}")
        except Exception as ex:
            raise ToolError(f"Error executing command '{command}': {str(ex)}")
    
    async def __call__(self, **kwargs) -> ToolResult:
        action = kwargs.get("action", "")
        return await asyncio.to_thread(self.execute_command, action)
    
    def to_params(self):
        return {"name": self.name, "type": "computer"}
