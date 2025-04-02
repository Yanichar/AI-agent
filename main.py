from typing import Optional
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from tools.factory import tool_factory
from tools.file_list import get_file_list
from tools.location import location_converter
from tools.weather import get_weather
from tools.time import get_time
from tools.file_reader import get_file_content
from tools.save_file import save_file_content


def chat_with_recursion(prompt, max_depth=50, current_depth=0, chat=None):
    if current_depth >= max_depth:
        return "Max recursion depth reached"

    if chat is None:
        chat = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.deepseek.com/",
        ).bind_tools(tool_factory.get_tools())

    messages = [HumanMessage(content=prompt)] if isinstance(prompt, str) else prompt

    response = chat.invoke(messages)

    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_messages = []
        for tool_call in response.tool_calls:
            if tool_call["name"] in tool_factory._tools:
                print(f"⚙️{tool_call['name']}, {tool_call['args']}")
                tool_result = tool_factory.invoke_tool(
                    tool_call["name"], tool_call["args"]
                )
                tool_messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
                )

        return chat_with_recursion(
            messages + [response] + tool_messages, max_depth, current_depth + 1, chat
        )

    return response.content


if __name__ == "__main__":
    while True:
        input_str = input("> ")

        result = chat_with_recursion(input_str)
        print(f"🤖{result}")
