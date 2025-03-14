# OmniTool AI Agent

## Overview
OmniTool is an AI-powered desktop automation tool leveraging OpenRouter vision-language models and OmniParser for computer interaction via GUI automation. It uses screenshots and UI element parsing to perform automated tasks such as clicking, typing, and navigation.

## Features
- GUI Automation via mouse and keyboard control
- Uses vision-language models to understand and interact with screen elements
- Real-time visual feedback with highlighted action targets
- Customizable agent logic and debugging info

## Prerequisites

### Required Software:
- Python 3.9+
- [OmniParser](https://github.com/omniparser/omniparser)
- An active [OpenRouter API](https://openrouter.ai/) key

### Python Dependencies:
```bash
pip install openai anthropic gradio pyautogui mss keyboard pillow requests
```

Ensure OmniParser server is running before starting the AI agent:
```bash
cd OmniParser/omnitool/omniparserserver
python omniparserserver.py
```

## Project Structure
```
agent/
├── AI_Agent/
│   ├── agent/
│   │   ├── llm_utils/
│   │   │   ├── openrouter_client.py
│   │   │   ├── omniparserclient.py
│   │   │   └── utils.py
│   │   └── openrouter_agent.py
│   ├── executor/
│   │   └── anthropic_executor.py
│   ├── tools/
│   │   ├── base.py
│   │   ├── computer.py
│   │   ├── screen_capture.py
│   │   ├── tool_collection.py
│   │   └── tool_result.py
│   ├── loop.py
│   ├── app.py
│   └── README.md
└── OmniParser/
    └── omniparserserver

```

## Usage
Run the AI Agent application:

```bash
cd AI_Agent
python app.py --windows_host_url localhost:8006 --omniparser_server_url localhost:8000 --server_port 7889
```

Visit `http://localhost:7889` to access the Gradio web interface.

### Keybindings
- **Stop Action**: Press the "Stop" button in the UI or hit `F2` twice rapidly (killswitch).

### Configuration
Configure your OpenRouter API key via the Gradio interface or by setting the environment variable:
```bash
export OPENROUTER_API_KEY='your-api-key-here'
```

## Debugging
Debug information and the selected UI element for interactions are displayed directly in the Gradio interface, under the "Local PC Control Active" section.

## Contributing
Feel free to open issues or submit pull requests for enhancements or bug fixes. Ensure any new features are well-documented and tested.

## License
Distributed under the MIT License. See `LICENSE` for more information.

