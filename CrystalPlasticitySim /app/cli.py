from app.config import apply_env, OPENAI_MODEL
from app.graph import build_graph

def run_query_through_graph(query: str, thread_id: int = 0):
    config = {"configurable": {"thread_id": str(thread_id)}, "recursion_limit": 200}
    graph = build_graph(openai_model=OPENAI_MODEL)
    for event in graph.stream({"messages": [("user", query)]}, subgraphs=True, config=config):
        print(event)
        print("----")

if __name__ == "__main__":
    import sys
    apply_env()
    q = sys.argv[1] if len(sys.argv) > 1 else "Hello"
    run_query_through_graph(q, thread_id=0)
