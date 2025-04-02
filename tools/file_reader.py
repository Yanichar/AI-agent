import os
import time
from charset_normalizer import from_bytes
from .factory import tool_factory


@tool_factory.register_tool(
    name="get_file_content",
    description="Get file content from specified path. Returns content as string or error message.",
)
def get_file_content(file_path: str) -> str:
    if not file_path or not isinstance(file_path, str):
        return "Error: Invalid file path provided"

    file_path = os.path.normpath(file_path)

    if not os.path.exists(file_path):
        return f"Error: File not found at path: {file_path}"

    if not os.path.isfile(file_path):
        return f"Error: Path is not a file: {file_path}"

    content = _ensure_read_file(file_path)

    if content is None:
        return f"Error: Could not read file at path: {file_path}"

    return content


def _ensure_read_file(path, max_attempts=120, sleep_interval=0.25, timeout=30):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return None

    start_time = time.time()
    attempts = 0

    while attempts < max_attempts:
        try:
            with open(path, "rb") as file:
                content = file.read()

                result = from_bytes(content).best()
                if result is None:
                    print(f"Unable to detect encoding for file: {path}")
                    return None

                encoding = result.encoding
                decoded_content = content.decode(encoding)
                decoded_content = decoded_content.replace("\r\n", "\n")
                return decoded_content

        except (IOError, OSError) as e:
            print(f"File reading error: {e}")
            time.sleep(sleep_interval)
            attempts += 1

        if time.time() - start_time > timeout:
            print(f"Timeout exceeded for file: {path}")
            break

    return None
