from typing import Optional
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from pyexpat.errors import messages
from pathlib import Path

from tools.factory import tool_factory
from tools.file_list import get_file_list
from tools.location import location_converter
from tools.weather import get_weather
from tools.time import get_time
from tools.file_reader import get_file_content
from tools.save_file import save_file_content

os.environ["TRANSFORMERS_VERBOSITY"] = "error"
import transformers

tokenizer = transformers.AutoTokenizer.from_pretrained(
    "./deepseek_v3_tokenizer", trust_remote_code=True
)


def count_tokens(text):
    return len(tokenizer.encode(text))


def chat_with_recursion(prompt, chat_history, max_depth=50, current_depth=0, chat=None):
    if current_depth >= max_depth:
        return "Max recursion depth reached"

    if chat is None:
        chat = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.deepseek.com/",
        ).bind_tools(tool_factory.get_tools())

    if prompt is not None:
        chat_history.append(HumanMessage(prompt))

    response = chat.invoke(chat_history)
    chat_history.append(response)

    if hasattr(response, "tool_calls") and response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] in tool_factory._tools:
                print(f"⚙️{tool_call['name']}, {tool_call['args']}")
                tool_result = tool_factory.invoke_tool(
                    tool_call["name"], tool_call["args"]
                )
                chat_history.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
                )

        return chat_with_recursion(
            None, chat_history, max_depth, current_depth + 1, chat
        )

    return response.content


def list_prompts():
    prompts_dir = Path("prompts")
    if not prompts_dir.exists():
        return []
    return [f.stem for f in prompts_dir.glob("*.txt")]


def load_prompt(prompt_name):
    prompt_path = Path("prompts") / f"{prompt_name}.txt"
    if not prompt_path.exists():
        return None
    with open(prompt_path, "r") as f:
        return f.read().strip()


def save_last_prompt(prompt_name):
    last_prompt_path = Path("last_prompt.txt")
    with open(last_prompt_path, "w") as f:
        f.write(prompt_name)


def load_last_prompt():
    last_prompt_path = Path("last_prompt.txt")
    if not last_prompt_path.exists():
        return None
    with open(last_prompt_path, "r") as f:
        return f.read().strip()


if __name__ == "__main__":
    # Load the last used prompt or default to "default"
    last_prompt_name = load_last_prompt() or "default"
    SYSTEM_PROMPT = load_prompt(last_prompt_name) or "You are helpful assistance."
    chat_history = [SystemMessage(SYSTEM_PROMPT)]

    print(f"Current prompt: {last_prompt_name}")

    COMMAND_HELP = """Available commands:
    - help: Show this help message
    - history: Show chat history
    - clear: Clear chat history and reset to initial state
    - prompts: List available system prompts
    - select <prompt_name>: Select a system prompt (e.g., 'select technical')
    - [any other input]: Process as normal chat message"""

    while True:
        input_str = input("> ").strip()

        if input_str == "history":
            if not chat_history:
                print("No chat history available")
            else:
                for i in chat_history:
                    print(str(type(i)).split(".")[-1], i.content)
                    print("")

        elif input_str == "clear":
            chat_history = [SystemMessage(SYSTEM_PROMPT)]
            print("Chat history cleared")

        elif input_str == "help":
            print(COMMAND_HELP)

        elif input_str == "prompts":
            prompts = list_prompts()
            if not prompts:
                print("No prompts available.")
            else:
                print("Available prompts:")
                for prompt in prompts:
                    print(f"- {prompt}")

        elif input_str.startswith("select "):
            prompt_name = input_str[len("select ") :].strip()
            new_prompt = load_prompt(prompt_name)
            if new_prompt is None:
                print(f"Prompt '{prompt_name}' not found.")
            else:
                SYSTEM_PROMPT = new_prompt
                chat_history = [SystemMessage(SYSTEM_PROMPT)]
                save_last_prompt(prompt_name)  # Save the selected prompt
                print(f"System prompt updated to '{prompt_name}'. Chat history cleared")

        else:
            output = chat_with_recursion(input_str, chat_history)
            print(f"🤖{output}")

            cumulative_tokens = sum(
                count_tokens(msg.content)
                for msg in chat_history
                if hasattr(msg, "content")
            )
            print(f"📊 Cumulative tokens in conversation: {cumulative_tokens}")
