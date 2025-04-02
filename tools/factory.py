from typing import Dict, Callable, Any
from langchain_core.tools import tool


class ToolFactory:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_descriptions: Dict[str, str] = {}

    def register_tool(self, name: str, description: str = "") -> Callable:
        def decorator(func: Callable) -> Callable:
            func.__name__ = name
            func.__doc__ = description
            tool_func = tool(func)

            self._tools[name] = tool_func
            self._tool_descriptions[name] = description

            return tool_func

        return decorator

    def get_tools(self) -> list:
        return list(self._tools.values())

    def invoke_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if tool_name not in self._tools:
            raise ValueError(f"Tool {tool_name} not registered")
        return self._tools[tool_name].invoke(args)


tool_factory = ToolFactory()
