from langgraph.graph import StateGraph, START, END

from state import ServiceDeskState
from agent import classify_issue, generate_response


graph = StateGraph(ServiceDeskState)

graph.add_node("classify_issue", classify_issue)
graph.add_node("generate_response", generate_response)

graph.add_edge(START, "classify_issue")
graph.add_edge("classify_issue", "generate_response")
graph.add_edge("generate_response", END)

app = graph.compile()


if __name__ == "__main__":

    user_input = input("\nDescribe your IT issue: ")

    result = app.invoke({
        "user_input": user_input
    })

    print("\n" + "=" * 50)
    print("AI IT SERVICE DESK")
    print("=" * 50)

    print(f"\nCategory : {result['category']}")
    print(f"Priority : {result['priority']}")

    print("\nAgent:")
    print(result["response"])

    print("\n" + "=" * 50)