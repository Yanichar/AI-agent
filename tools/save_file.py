import os
from typing import Optional
from pathlib import Path
from .factory import tool_factory


@tool_factory.register_tool(
    name="save_file_content",
    description="Save content to a file at specified path. Creates directories if needed. Returns success message or error.",
)
def save_file_content(
    file_path: str, content: str, overwrite: Optional[bool] = False
) -> str:
    try:
        if not file_path or not isinstance(file_path, str):
            return "Error: Invalid file path provided"

        if content is None:
            return "Error: No content provided to write"

        file_path = os.path.normpath(file_path)
        path_obj = Path(file_path)

        if path_obj.exists() and path_obj.is_dir():
            return f"Error: Path is a directory: {file_path}"

        if path_obj.exists() and path_obj.is_file() and not overwrite:
            return f"Error: File already exists at {file_path} (use overwrite=True to replace)"

        parent_dir = path_obj.parent
        if not parent_dir.exists():
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return f"Error creating directories: {str(e)}"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully saved content to {file_path}"
        except (IOError, OSError) as e:
            return f"Error writing file: {str(e)}"

    except Exception as e:
        return f"Unexpected error saving file: {str(e)}"
