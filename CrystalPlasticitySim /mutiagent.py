from typing import Literal
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver

import getpass
import os
from langgraph.types import Command

from typing import Annotated

from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from workdir.damask_yaml import update_material_properties
from workdir.damask_yaml import update_load_yaml
from workdir.damask_simulation import run_damask_simulation
from workdir.damask_results import calculate_deviation_angle

from tempfile import TemporaryDirectory

from langchain_community.agent_toolkits import FileManagementToolkit
import os
import json
from datetime import datetime

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "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" 
os.environ["LANGCHAIN_PROJECT"] = "damask_agent_v9" 



memory = MemorySaver()

# This executes code locally, which can be unsafe
repl = PythonREPL()


@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate program."],
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    result_str = f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"
    return result_str



from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import MessagesState, END
from langgraph.types import Command


members = ["simulator", "coder"]
# Our team supervisor is an LLM node. It just picks the next agent to process
# and decides when the work is completed
options = members + ["FINISH"]

system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    f" following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)

from pydantic import BaseModel, Field


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal[*options]


llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.2,
    max_tokens=None,
    timeout=None,
    max_retries=40,
    api_key="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",
    verbose=True,
)


class State(MessagesState):
    next: str



def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    if goto == "FINISH":
        goto = END

    return Command(goto=goto, update={"next": goto})

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent

damask_agent_prompt = (
    "You are an expert in materials science specializing in crystal plasticity modeling."
    " Your role is to analyze and simulate material behaviors using the following tools:"
    " Given a user request, select the most appropriate tool(s) to process the task."
    " Provide detailed and structured results based on scientific best practices."
)

damask_agent = create_react_agent(
    llm, tools=[
        update_load_yaml,
        run_damask_simulation,
        calculate_deviation_angle,update_material_properties], prompt=damask_agent_prompt
)


def damask_node(state: State) -> Command[Literal["supervisor"]]:
    result = damask_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="simulator")
            ]
        },
        goto="supervisor",
    )

code_agent_prompt = (
    "You are an expert Python programmer specializing in numerical optimization."
    " Your role is to generate, modify, and execute scripts efficiently within a specified `workdir` directory."
    " The `workdir` directory contains all necessary input files, and all operations should be performed using absolute paths."
    " You will work with libraries like SciPy, PuLP, Pyomo, and CVXPY for optimization."
    " Follow these structured steps strictly:"
    
    " 1. Scan and analyze existing Python files inside the `workdir` directory to identify reusable functions and modules."
    " 2. Select and import relevant functions with 'import' statements from local files within `workdir` instead of redefining them."
    " 3. All input and output files should be handled using absolute paths within `workdir`."
    " 4. Generate a complete, well-documented Python script with a structured main execution block."
    " 5. Automatically check to install any missing dependencies required for execution and detect to import them."
    " 6. If errors occur during execution:"
    "    - Generate a new version of the script with names 'version_1', 'version_2', etc.,"
    "      instead of overwriting the original script when debug the code."
    "    - Retry execution with the revised script."
)



code_agent_tool = []
toolkit = FileManagementToolkit(
    root_dir= os.getcwd()
)  # If you don't provide a root_dir, operations will default to the current working directory
code_agent_tool += toolkit.get_tools()
code_agent_tool += [python_repl_tool]

# NOTE: THIS PERFORMS ARBITRARY CODE EXECUTION, WHICH CAN BE UNSAFE WHEN NOT SANDBOXED
code_agent = create_react_agent(llm, tools=code_agent_tool, prompt=code_agent_prompt)


def filter_messages(messages: list):
    # This is very simple helper function which only ever uses the last message
    return messages[-1:]

def code_node(state: State) -> Command[Literal["supervisor"]]:
    result = code_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="coder")
            ]
        },
        goto="supervisor",
    )


def build_graph():
    builder = StateGraph(State)
    builder.add_edge(START, "supervisor")
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("simulator", damask_node)
    builder.add_node("coder", code_node)
    return builder.compile(checkpointer=memory)


# Logging utilities
def log_query(query: str, log_file: str = "query_response_log.txt"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"Timestamp: {timestamp}\nQuery: {query}\n{'-' * 50}\n"
    with open(log_file, "a") as log:
        log.write(log_entry)

def log_response(response: str, log_file: str = "query_response_log.txt"):
    log_entry = f"{response}\n{'-' * 50}\n"
    with open(log_file, "a") as log:
        log.write(log_entry)

# Build the graph only once
graph = build_graph()

# Function to run a query through the graph
def run_query_through_graph(query: str, thread_id: int):
    log_query(query)

    config = {
        "configurable": {
            "thread_id": str(thread_id)
        },
        "recursion_limit": 200
    }

    for event in graph.stream({"messages": [("user", query)]}, subgraphs=True, config=config):
        print(event)
        print("----")
        log_response(event)
