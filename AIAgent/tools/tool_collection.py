from .computer import ComputerTool

class ToolCollection:
    def __init__(self, tool=None):
        self.tool = tool or ComputerTool()

    async def run(self, name, tool_input):
        return await self.tool(**tool_input)
