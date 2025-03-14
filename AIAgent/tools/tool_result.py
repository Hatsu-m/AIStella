class ToolResult:
    def __init__(self, output=None, error=None, base64_image=None, system=None):
        self.output = output
        self.error = error
        self.base64_image = base64_image
        self.system = system
