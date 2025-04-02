import os
from typing import List
from .factory import tool_factory


@tool_factory.register_tool(
    name="get_file_list",
    description="Get list of files and directory in specific directory",
)
def get_file_list(directory: str = ".") -> str:
    try:
        if not os.path.exists(directory):
            return f"Directory not found: {directory}"

        if not os.path.isdir(directory):
            return f"Path is not a directory: {directory}"

        entries = os.listdir(directory)

        files = []
        dirs = []

        for entry in entries:
            full_path = os.path.join(directory, entry)
            if os.path.isdir(full_path):
                dirs.append(entry + "/")
            else:
                files.append(entry)

        dirs.sort()
        files.sort()

        output = []
        if dirs:
            output.append("Directories:")
            output.extend([f"- {d}" for d in dirs])
        if files:
            if output:
                output.append("")
            output.append("Files:")
            output.extend([f"- {f}" for f in files])

        if not output:
            return f"No files found in directory: {directory}"

        return "\n".join(output)

    except PermissionError:
        return f"Permission denied accessing directory: {directory}"
    except Exception as e:
        return f"Error listing files: {str(e)}"
