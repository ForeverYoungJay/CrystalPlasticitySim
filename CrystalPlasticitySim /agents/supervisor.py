from typing import Literal
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langgraph.graph import MessagesState, END
from prompt import SUPERVISOR_PROMPT

class Router(TypedDict):
    next: Literal["simulator", "coder", "FINISH"]

def make_supervisor_llm(model="gpt-4o"):
    return ChatOpenAI(model=model, temperature=0.2, max_retries=40)

def supervisor_node(state: MessagesState, llm) -> Command[Literal["simulator","coder","__end__"]]:
    workers = ["simulator", "coder"]
    system_prompt = SUPERVISOR_PROMPT.format(workers=workers)
    messages = [{"role": "system", "content": system_prompt}] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    if goto == "FINISH":
        goto = END
    return Command(goto=goto, update={"next": goto})
