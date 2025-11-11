from typing import Annotated
from langchain_experimental.utilities import PythonREPL
from langchain_core.tools import tool
from langchain_community.agent_toolkits import FileManagementToolkit
import os

repl = PythonREPL()
toolkit = FileManagementToolkit(root_dir=os.getcwd())
FILE_TOOLS = toolkit.get_tools()

@tool
def python_repl_tool(code: Annotated[str, "Python code to execute."]):
    """Executes Python code and returns stdout."""
    try:
        out = repl.run(code)
        return f"Successfully executed:\n```python\n{code}\n```\nStdout: {out}"
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"

EXTRA_TOOLS = [python_repl_tool]
