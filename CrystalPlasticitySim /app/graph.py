from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from agents.supervisor import make_supervisor_llm, supervisor_node
from agents.simulation_agent import make_damask_agent, damask_node
from agents.code_agent import make_code_agent, code_node

class State(MessagesState):
    next: str

def build_graph(openai_model="gpt-4o"):
    memory = MemorySaver()

    llm = make_supervisor_llm(model=openai_model)
    damask_agent = make_damask_agent(llm)
    code_agent = make_code_agent(llm)

    def supervisor(s): return supervisor_node(s, llm)
    def simulator(s):  return damask_node(s, damask_agent)
    def coder(s):      return code_node(s, code_agent)

    builder = StateGraph(State)
    builder.add_edge(START, "supervisor")
    builder.add_node("supervisor", supervisor)
    builder.add_node("simulator", simulator)
    builder.add_node("coder", coder)
    return builder.compile(checkpointer=memory)
