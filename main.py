from langgraph.graph import StateGraph, START, END
from rag import retrieve_context

from state import ServiceDeskState
from agent import (
    classify_issue,
    route_issue,
    escalation_response,
    self_service_response,
    retrieve_knowledge
)


def route_after_classification(state: ServiceDeskState):

    if state["next_action"] == "escalate":
        return "escalate"

    return "self_service"


graph = StateGraph(ServiceDeskState)

# Nodes
graph.add_node("classify_issue", classify_issue)
graph.add_node("route_issue", route_issue)
graph.add_node("escalate", escalation_response)
graph.add_node("self_service", self_service_response)
graph.add_node("retrieve_knowledge", retrieve_knowledge)

# Flow
graph.add_edge(START, "classify_issue")
graph.add_edge("classify_issue", "retrieve_knowledge")
graph.add_edge("retrieve_knowledge", "route_issue")

# Conditional routing
graph.add_conditional_edges(
    "route_issue",
    route_after_classification,
    {
        "escalate": "escalate",
        "self_service": "self_service"
    }
)

graph.add_edge("escalate", END)
graph.add_edge("self_service", END)

app = graph.compile()


if __name__ == "__main__":

    user_input = input("\nDescribe your IT issue: ")

    result = app.invoke({
        "user_input": user_input
    })

    print("\n" + "=" * 50)
    print("AI IT SERVICE DESK")
    print("=" * 50)

    print(f"\nCategory    : {result['category']}")
    print(f"Priority    : {result['priority']}")
    print(f"Next Action : {result['next_action']}")

    print("\nAgent:")
    print(result["response"])

    print("\n" + "=" * 50)