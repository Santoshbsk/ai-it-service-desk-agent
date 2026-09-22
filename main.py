from langgraph.types import Command
from config import validate_config
from agent import app



if __name__ == "__main__":
    validate_config()
    #Configure the graph with a unique thread ID for this session
    config = {
        "configurable": {
            "thread_id": "service-desk-001"
        }
        }

    first_request = True

    while True:
        user_input = input("\nDescribe your Query (exit/quit to stop): ")

        if user_input.lower() in ["exit", "quit"]:
            break
        
        #Apply the configuration and invoke the graph with the user input
        initialstate = { #Configure the initial state with the user input
            "user_input": user_input,
            "category": "",
            "priority": "",
            "response": "",
            "next_action": "",
            "retrieved_context": [],
            "tool_required": False,
            "tool_name": "none",
            "tool_result": {},
            "approval_required": False,
            "ticket_id": "",
            "ticket_status": "",
            "ticket_history": [],
            "ticket_reference": "",
            "clarification_required": False,
            "duplicate_ticket": False,
            "duplicate_ticket_id": "",  
            "issue_type": "",
            "requested_status": "",
            "status_transition_valid": False,
            "tool_success": True,
            "tool_error": "",
            "retry_count": 0,
            "audit_log": [],
            "decision_trace": [],
            "tool_error_type":""
        }
        if first_request:
            print("\n" + "=" * 50)
            print("AI IT SERVICE DESK")
            print("=" * 50)
            first_request = False
            result = app.invoke(initialstate,config=config)

        else:
            result = app.invoke({"user_input": user_input},config=config)

        if result.get("__interrupt__"):

            interrupt_data = result["__interrupt__"][0]

            print("\n" + "=" * 60)
            print("HUMAN APPROVAL REQUIRED")
            print("=" * 60)

            print(interrupt_data.value)

            user_res = input("\nYour response: ")
            print("\n" + "=" * 60)
            print("User Respone Received:  " + user_res)
            result = app.invoke(
                Command(resume=user_res),
                config=config
            )

        print("\n" + "=" * 50)
        print("AI IT SERVICE DESK")
        print("=" * 50)

        print(f"\nCategory    : {result['category']}")
        print(f"Priority    : {result['priority']}")

        if result.get("tool_required"):
            print("Action      : Tool execution")
            print(f"Tool        : {result['tool_name']}")
        else:
            print(f"Next Action : {result['next_action']}")

        print("\nAgent:")
        print(result["response"])
        print("\n" + "=" * 50)
        print("\nDecision Trace:")

        for i, trace in enumerate(result.get("decision_trace", []), start=1):

            print(
                f"{i}. {trace['step']}: "
                f"{trace['decision']}"
            )