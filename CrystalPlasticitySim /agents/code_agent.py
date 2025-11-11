from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from prompt import CODE_AGENT_PROMPT
from app.tools import FILE_TOOLS, EXTRA_TOOLS

def make_code_agent(llm):
    tools = FILE_TOOLS + EXTRA_TOOLS
    return create_react_agent(llm, tools=tools, prompt=CODE_AGENT_PROMPT)

def code_node(state, code_agent) -> Command:
    result = code_agent.invoke(state)
    return Command(
        update={"messages": [HumanMessage(content=result["messages"][-1].content, name="coder")]},
        goto="supervisor",
    )
