from typing import Literal
from unittest import result
from langgraph.types import interrupt
from langgraph.graph import StateGraph, START, END
from rag import retrieve_context
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, Interrupt


from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

from state import ServiceDeskState
from config import GEMINI_API_KEY, LLM_MODEL

from rag import retrieve_context

from tools import check_disk_space, check_network_status, create_service_ticket, check_ticket_status, update_ticket_status

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime,timezone

llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=0
)


class IssueClassification(BaseModel):
    category: Literal[
        "Hardware",
        "Software",
        "Network",
        "Access",
        "Security",
        "Other"
    ]

    issue_type: Literal[
        "VPN",
        "Laptop Performance",
        "Password Reset",
        "Software Installation",
        "Email",
        "Other"
    ]

    priority: Literal[
        "Low",
        "Medium",
        "High",
        "Critical"
    ]

classifier = llm.with_structured_output(IssueClassification)

class ToolDecision(BaseModel):
    tool_required: bool = Field(
        description="Whether a tool is required to answer the user's request"
    )

    tool_name: Literal[
        "check_disk_space",
        "check_network_status",
        "create_service_ticket",
        "check_ticket_status",
        "update_ticket_status",
        "none"
    ] = Field(
        description="The tool that should be executed"
    )

    ticket_reference: str = Field(
        default="",
        description=(
            "The ticket ID or description of the ticket the user "
            "is referring to. Examples: INC-12345678, VPN ticket, "
            "software installation ticket."
        )
    )

    new_ticket_status: Literal[
    "Created",
    "In Progress",
    "Resolved",
    "Closed",
    ""
    ] = Field(
        default="",
        description="The new status requested by the employee"
    )

tool_decider = llm.with_structured_output(ToolDecision)

def execute_tool(state: ServiceDeskState):
    try:


            if state["tool_name"] == "check_disk_space":

                result = check_disk_space()

            elif state["tool_name"] == "check_network_status":
                result = check_network_status()

            elif state["tool_name"] == "create_service_ticket":
                
                result = create_service_ticket(
                    issue=state.get("user_input"),
                    category=state.get("category"),
                    priority=state.get("priority"),
                    issue_type=state.get("issue_type")
                )
                if "error" in result:
                    return {
                        "tool_result": result,
                        "tool_success": False,
                        "tool_error": result["error"],
                        "tool_error_type": result.get(
                            "error_type",
                            "unknown"
                        )
                    }
                ticket = {
                "ticket_id": result["ticket_id"],
                "status": result["status"],
                "issue": state["user_input"],
                "category": state["category"],
                "priority": state["priority"],
                "issue_type": state["issue_type"]
                }

                history = state.get("ticket_history", [])

            # history.append(ticket)

                return {
                "tool_result": result,
                "ticket_id": result["ticket_id"],
                "ticket_status": result["status"],
                "ticket_history": history + [ticket],
                "tool_success": True,
                "tool_error": "",
                "tool_error_type": ""

                }
            elif state["tool_name"] == "check_ticket_status":

                ticket_id = state.get("ticket_id", "")

                if not ticket_id:

                    return {
                        "tool_result": {
                            "error": "No matching ticket was found."
                        },
                        "tool_success": False,
                        "tool_error": "No matching ticket was found."
                    }

                result = check_ticket_status(ticket_id)

                if "error" in result:
                     return {
                        "tool_result": result,
                        "tool_success": False,
                        "tool_error": result["error"],
                        "tool_error_type": result.get("error_type","unknown")
                        }
                return {
                    "tool_result": result,
                    "tool_success": True,
                    "tool_error": "",
                    "tool_error_type": "",
                    "ticket_status": result["status"]
                }

            elif state["tool_name"] == "update_ticket_status":

                ticket_id = state["ticket_id"]
                new_status = state["requested_status"]

                result = update_ticket_status(
                    ticket_id=ticket_id,
                    new_status=new_status
                )

                if "error" in result:
                    return {
                        "tool_result": result,
                        "tool_success": False,
                        "tool_error": result["error"],
                        "tool_error_type": result.get(
                            "error_type",
                            "unknown"
                        )
                    }

                history = state.get("ticket_history", [])

                updated_history = []

                for ticket in history:

                    if ticket["ticket_id"] == ticket_id:

                        updated_ticket = ticket.copy()
                        updated_ticket["status"] = new_status

                        updated_history.append(updated_ticket)

                    else:
                        updated_history.append(ticket)

                return {
                    "tool_result": result,
                    "ticket_status": new_status,
                    "ticket_history": updated_history,
                    "tool_success": True,
                    "tool_error": "",
                    "tool_error_type": ""
                }

            else:

                result = {
                    "error": f"Unknown tool: {state['tool_name']}"
                }
            #print("result::"+result)
            return {
                    "tool_result": result,
                    "decision_trace": state.get("decision_trace", []) + [
                        {
                            "step": "tool_execution",
                            "decision": (
                                f"{state['tool_name']} executed successfully"
                            )
                        }
                    ]
            }
    except Exception as e:
        return {
            "tool_result": {},
            "tool_success": False,
            "tool_error": str(e),
            "decision_trace": state.get("decision_trace", []) + [
                {
                    "step": "tool_execution",
                    "decision": (
                        f"{state['tool_name']} execution failed: {str(e)}"
                    )
                }
            ]
        }

def tool_response(state: ServiceDeskState):

    tool_name = state["tool_name"]
    result = state["tool_result"]

    if tool_name == "check_disk_space":

        free_gb = result.get("free_gb")

        if free_gb is None:
            return {
                "response": "I was unable to retrieve the disk space information."
            }

        if free_gb < 10:

            message = (
                f"Your C: drive has only {free_gb} GB of free space.\n\n"
                "This is relatively low and may affect laptop performance.\n\n"
                "Recommended next steps:\n"
                "1. Close unnecessary applications.\n"
                "2. Use approved disk cleanup methods.\n"
                "3. Do not manually delete system files.\n"
                "4. Contact Desktop Support if additional assistance is required."
            )

        else:

            message = (
                f"Your C: drive currently has {free_gb} GB of free space.\n\n"
                "The available disk space does not appear to be critically low."
            )

        return {
            "response": message
        }

    elif tool_name == "check_network_status":

        status = result.get("status")
        network_message = result.get("message")

        if status == "Connected":

            message = (
                "I checked your network connectivity.\n\n"
                f"{network_message}\n\n"
                "Your basic network connection appears to be available."
            )

        else:

            message = (
                "I checked your network connectivity.\n\n"
                f"{network_message}\n\n"
                "Please check your network connection or contact IT Support "
                "if the issue continues."
            )

        return {
            "response": message
        }
    elif tool_name == "create_service_ticket":
        ticket_id = result.get("ticket_id")
        status = result.get("status")
        message = result.get("message")

        if ticket_id and status == "Created":
            response_message = (
                f"A service ticket has been created successfully.\n\n"
                f"Ticket ID: {ticket_id}\n"
                f"Status: {status}\n"
                f"Message: {message}\n\n"
                "Please keep this ticket ID for your records."
            )
        else:
            response_message = (
                "There was an issue creating the service ticket.\n\n"
                "Please try again later or contact IT Support."
            )

        return {
            "response": response_message
        }
    elif tool_name == "check_ticket_status":
        ticket_id = state.get("ticket_id", "")

        if not ticket_id:
                return {
                    "tool_result": {
                        "error": "No matching ticket was found."
                    }
            }

        result = check_ticket_status(ticket_id)

    
        response_message = (f"Here is the current status of your service ticket:\n\n"
        f"Ticket ID: {result['ticket_id']}\n"
        f"Status: {result['status']}\n"
        f"Message: {result['message']}")
        return {
            "response": response_message
        }

    elif state["tool_name"] == "update_ticket_status":

        result = state["tool_result"]

        if "error" in result:
            return {
                "response": result["error"]
            }

        return {
            "response": (
                f"Ticket {result['ticket_id']} "
                f"has been updated to {result['status']}."
            )
        }

    else:

        return {
            "response": "The requested tool could not be processed."
        }

def decide_tool(state: ServiceDeskState):

    user_input = state["user_input"]

    prompt = f"""
You are an IT Service Desk agent.

Determine whether a tool is required to answer the employee's request.

Available tool:

1. check_disk_space
   - Checks the available disk space on the employee's C: drive.
   - Use this when the employee asks about disk space, storage,
     low disk space, insufficient storage, or similar issues.

2. check_network_status
   - Checks the network connectivity status.
   - Use this when the employee reports network connectivity issues,
     such as being unable to access the internet or internal resources.

3. create_service_ticket
   - Creates a service ticket for the employee's issue.
   - Use explicitly when the employee requests a service ticket to be created or submitted.

4. check_ticket_status
   - Checks the status of an existing service ticket.
   - Use when the employee asks about the status of a ticket.

5. update_ticket_status
   - Updates the status of an existing service ticket.
   - Use when the employee requests to change the status of a ticket.


If no tool is required, select "none".

IMPORTANT TOOL SELECTION RULES:

1. Do NOT select a tool merely because the user's issue relates to
   the tool's domain.

2. "My VPN is not working" is NOT an explicit request to check network
   connectivity. Return tool_name="none".

3. Select check_network_status only when the user explicitly asks to
   check, test, verify, or diagnose their network/internet connectivity.

4. Select check_disk_space only when the user explicitly asks to check
   their disk/storage space.

5. Select create_service_ticket only when the user explicitly asks to
   create, raise, submit, or open a service ticket.

6. Select check_ticket_status when the user asks for the status or
   progress of an existing ticket.

7. Select update_ticket_status only when the user explicitly asks to
   resolve, close, or change the status of an existing ticket.

8. If the user is only asking for troubleshooting instructions,
   explanation, or general information, return tool_name="none".

Employee request:
{user_input}
"""

    result = tool_decider.invoke(prompt)
    trace = state.get("decision_trace", [])
    
    if result.tool_name == "none":
            return {
                "tool_required": False,
                "tool_name": "",
                "ticket_reference": "",
                "requested_status": "",
                "decision_trace": trace + [
                    {
                        "step": "tool_decision",
                        "decision": "No tool required"
                    }
                ]
            }

   
    
    trace_entry = {
            "step": "tool_decision",
            "decision": (
                f"Tool={result.tool_name}, "
                f"Required={result.tool_required}"
            )
            }
    return {
        "tool_required": result.tool_required,
        "tool_name": result.tool_name,
        "ticket_reference": result.ticket_reference,
        "requested_status": result.new_ticket_status,
        "decision_trace": trace + [trace_entry]
    }


def check_duplicate_ticket(state: ServiceDeskState):
    #   This function checks if there is an existing ticket in the session history  
    #   that matches the current issue type and is still active (i.e., not resolved or closed).

    history = state.get("ticket_history", [])
    current_issue_type = state["issue_type"]

    active_statuses = {
        "Created",
        "In Progress"
    }

    for ticket in history:

        if (
            ticket["issue_type"] == current_issue_type
            and ticket["status"] in active_statuses
        ):

            return {
                "duplicate_ticket": True,
                "duplicate_ticket_id": ticket["ticket_id"],
                "decision_trace": state.get("decision_trace", []) + [
                    {
                        "step": "duplicate_check",
                        "decision": (
                            f"Active duplicate found: "
                            f"{ticket['ticket_id']} "
                            f"({current_issue_type})"
                        )
                    }
                ]
            }

    return {
        "duplicate_ticket": False,
        "duplicate_ticket_id": "",
        "decision_trace": state.get("decision_trace", []) + [
            {
                "step": "duplicate_check",
                "decision": (
                    f"No active duplicate found for "
                    f"{current_issue_type}"
                )
            }
        ]
    }

def resolve_ticket_reference(state: ServiceDeskState):
#    This function attempts to resolve a ticket reference provided by the user.
    reference = state.get("ticket_reference", "").lower().strip()
    history = state.get("ticket_history", [])
    multiple_tickets = False
    if not history:
        return {
            "ticket_id": "",
            "status": "",
            "response": (
                "I could not find any service tickets in this session."
            )
        }

    # 1. Exact ticket ID match
    for ticket in history:

        if ticket["ticket_id"].lower() == reference:
            return {
                "ticket_id": ticket["ticket_id"],
                "ticket_status": ticket["status"],
                "classification_required": False,
                "decision_trace": state.get("decision_trace", []) + [
                    {
                        "step": "ticket_resolution",
                        "decision": (
                            f"Exact ticket ID match: "
                            f"{ticket['ticket_id']}"
                        )
                    }
                ]
            }

    # 2. Remove generic words from the reference
    reference_words = set(
        word
        for word in reference.split()
        if word not in {
            "my",
            "the",
            "a",
            "an",
            "ticket",
            "issue",
            "request",
            "status"
        }
    )

    # 3. Find all matching tickets
    matching_tickets = []

    for ticket in history:

        searchable_text = (
            ticket["issue"] + " " +
            ticket["category"]
        ).lower()

        if reference_words and all(
            word in searchable_text
            for word in reference_words
        ):
            matching_tickets.append(ticket)

    # 4. Exactly one match
    if len(matching_tickets) == 1:

        return {
            "ticket_id": matching_tickets[0]["ticket_id"],
            "ticket_status": matching_tickets[0]["status"],
            "classification_required": False,
            "decision_trace": state.get("decision_trace", []) + [
                {
                    "step": "ticket_resolution",
                    "decision": (
                        f"Single matching ticket found: "
                        f"{ticket['ticket_id']}"
                    )
                }
            ]
        }

    # 5. Multiple matches → clarification required
    if len(matching_tickets) > 1:
        multiple_tickets = True;
        ticket_list = "\n".join(
            f"{i + 1}. {ticket['ticket_id']} "
            f"- {ticket['issue']}"
            for i, ticket in enumerate(matching_tickets)
        )

        return {
            "ticket_id": "",
            "ticket_status": "",
            "response": (
                "I found multiple tickets that may match your request:\n\n"
                f"{ticket_list}\n\n"
                "Please provide the ticket ID you want me to check."
            ),
            "clarification_required": multiple_tickets,
            "decision_trace": state.get("decision_trace", []) + [
                {
                    "step": "ticket_resolution",
                    "decision": (
                        f"Multiple matching tickets found "
                        f"({len(matching_tickets)}); "
                        "clarification required"
                    )
                }
            ]
        }

    # 6. Generic request → latest ticket
    if reference in [
        "",
        "my ticket",
        "ticket",
        "latest ticket",
        "my latest ticket"
    ]:

        return {
            "ticket_id": history[-1]["ticket_id"],
            "ticket_status": history[-1]["status"],
            "classification_required": False,
            "decision_trace": state.get("decision_trace", []) + [
                {
                    "step": "ticket_resolution",
                    "decision": (
                        f"Generic request; "
                        f"using latest ticket: "
                        f"{history[-1]['ticket_id']}"
                    )
                }
            ]
        }

    # 7. No match
    return {
        "ticket_id": "",
        "ticket_status": "",
        "response": (
            "I couldn't identify which ticket you are referring to. "
            "Please provide the ticket ID or describe the issue."
        ),
        "classification_required": False,
        "decision_trace": state.get("decision_trace", []) + [
            {
                "step": "ticket_resolution",
                "decision": (
                    "No matching ticket found; "
                    "clarification required"
                )
            }
        ]
    }



def retrieve_knowledge(state: ServiceDeskState):

    results = retrieve_context(
        state["user_input"],
        k=3
    )

    contexts = []

    for doc in results:
        contexts.append({
            "content": doc.page_content,
            "source": doc.metadata.get("source", "Unknown")
        })

    return {
        "retrieved_context": contexts
    }

def classify_issue(state: ServiceDeskState):

    prompt = f"""
You are an enterprise IT Service Desk classification agent.

Analyze the employee's issue and classify it.

Employee issue:
{state["user_input"]}

Classification rules:

Critical:
- Major security incident
- Company-wide outage
- Critical production impact
- Data loss or suspected breach

High:
- Employee cannot work
- Major system/application unavailable
- Important security update cannot be installed
- Significant business impact

Medium:
- Issue affects productivity but employee can continue working
- Non-critical software problems
- Intermittent issues

Low:
- General questions
- Minor inconvenience
- Informational requests

Return the appropriate category and priority.
"""

    result = classifier.invoke(prompt)

    return {
        "category": result.category,
        "issue_type": result.issue_type,
        "priority": result.priority,
        "decision_trace": state.get("decision_trace", []) + [
        {
            "step": "classification",
            "decision": (
                f"Category={result.category}, "
                f"IssueType={result.issue_type}, "
                f"Priority={result.priority}"
            )
        }
    ]
    }


def route_issue(state: ServiceDeskState):

    if state["priority"] in ["High", "Critical"]:

        return {
            "next_action": "escalate",
            "decision_trace": state.get("decision_trace", []) + [
                {
                    "step": "routing",
                    "decision": (
                        f"Escalate because priority is "
                        f"{state['priority']}"
                    )
                }
            ]
        }

    return {
        "next_action": "self_service",
        "decision_trace": state.get("decision_trace", []) + [
            {
                "step": "routing",
                "decision": (
                    f"Self-service because priority is "
                    f"{state['priority']}"
                )
            }
        ]
    }

def escalation_response(state: ServiceDeskState):

    prompt = f"""
You are an enterprise IT Service Desk Agent.

The employee reported:

{state["user_input"]}

Category: {state["category"]}
Priority: {state["priority"]}

This issue requires escalation.

Write a concise professional response explaining that
the issue requires priority support.

Do NOT claim that a real ticket was created.
Do NOT claim that a technician was contacted.

Return only the response.
"""

    result = llm.invoke(prompt)

    if isinstance(result.content, list):
        text = "".join(
            block.get("text", "")
            if isinstance(block, dict)
            else str(block)
            for block in result.content
        )
    else:
        text = str(result.content)

    return {
        "response": text.strip()
    }


def self_service_response(state: ServiceDeskState):

    context = "\n\n".join(
        [
            f"Source: {item['source']}\n{item['content']}"
            for item in state["retrieved_context"]
        ]
    )

    prompt = f"""
You are an enterprise IT Service Desk Agent.

Employee issue:

{state["user_input"]}

Category:
{state["category"]}

Priority:
{state["priority"]}

Use ONLY the following IT knowledge base information
to provide troubleshooting guidance.

KNOWLEDGE BASE:

{context}

Rules:

1. Do not invent troubleshooting steps.
2. Do not claim that an action has been performed.
3. If the knowledge base does not contain enough information,
   clearly say that additional IT support is required.
4. Mention the relevant knowledge-base source.
5. Give clear numbered troubleshooting steps.
6. Format sources like:

Sources:
- filename.txt

If the knowledge base does not contain enough information,
say that additional IT support is required.

Return only the final response.
"""

    result = llm.invoke(prompt)

    if isinstance(result.content, list):
        text = "".join(
            block.get("text", "")
            if isinstance(block, dict)
            else str(block)
            for block in result.content
        )
    else:
        text = str(result.content)

    return {
        "response": text.strip()
    }

def request_approval(state: ServiceDeskState):

    approval_message = (
        "\n⚠️ APPROVAL REQUIRED\n\n"
        "The agent is requesting permission to create an IT service ticket.\n\n"
        f"Category : {state['category']}\n"
        f"Priority : {state['priority']}\n"
        f"Issue    : {state['user_input']}\n\n"
        "Do you want to create this ticket?\n"
        "Reply with: yes or no"
    )

    decision = interrupt(approval_message)

    if isinstance(decision, str):
        decision = decision.lower().strip()

    if decision in ["yes", "y"]:

        return {
            "approval_required": True,
            "approval_status": "approved",
            "decision_trace": state.get("decision_trace", []) + [
                {
                    "step": "human_approval",
                    "decision": "Ticket creation approved by user"
                }
            ]
        }

    return {
        "approval_required": True,
        "approval_status": "rejected",
        "response": (
            "The service ticket was not created because "
            "approval was not provided."
        ),
        "decision_trace": state.get("decision_trace", []) + [
            {
                "step": "human_approval",
                "decision": "Ticket creation rejected by user"
            }
        ]
    }


def request_ticket_clarification(state: ServiceDeskState):

    clarification_message = (
        "\n⚠️ CLARIFICATION REQUIRED\n\n"
        "I found multiple tickets that may match your request.\n\n"
        f"{state['response']}\n\n"
        "Please provide the ticket ID."
    )

    ticket_id = interrupt(clarification_message)
    print(f"User provided ticket ID: {ticket_id}")
    return {
        "ticket_id": str(ticket_id).strip(),
        "clarification_required": False,
        "decision_trace": state.get("decision_trace", []) + [
            {
                "step": "ticket_clarification",
                "decision": (
                    f"User provided ticket ID: {ticket_id}"
                )
            }
        ]
    }

def duplicate_ticket_response(state: ServiceDeskState):

    ticket_id = state["duplicate_ticket_id"]

    return {
        "response": (
            f"An active ticket already exists for this issue.\n\n"
            f"Ticket ID : {ticket_id}\n"
            f"Issue Type: {state['issue_type']}\n\n"
            "I will not create a duplicate ticket. "
            "Please continue using the existing ticket."
        )
    }

def validate_status_transition(state: ServiceDeskState):

    current_status = state.get("ticket_status", "")
    requested_status = state.get("requested_status", "")

    valid_transitions = {
        "Created": ["In Progress"],
        "In Progress": ["Resolved"],
        "Resolved": ["Closed"],
        "Closed": []
    }

    allowed_statuses = valid_transitions.get(current_status, [])

    if requested_status in allowed_statuses:

        return {
            "response": "",
            "status_transition_valid": True,
            "decision_trace": state.get("decision_trace", []) + [
                {
                    "step": "status_validation",
                    "decision": (
                        f"Allowed transition: "
                        f"{current_status} → {requested_status}"
                    )
                }
            ]
        }

    return {
        "status_transition_valid": False,
        "response": (
            f"Invalid ticket status transition.\n\n"
            f"Current status  : {current_status}\n"
            f"Requested status: {requested_status}\n\n"
            f"Allowed next status: "
            f"{', '.join(allowed_statuses) if allowed_statuses else 'None'}"
        ),
        "decision_trace": state.get("decision_trace", []) + [
        {
            "step": "status_validation",
            "decision": (
                f"Blocked transition: "
                f"{current_status} → {requested_status}"
            )
        }
        ]
    }

def prepare_tool_retry(state: ServiceDeskState):

    return {
        "retry_count": state.get("retry_count", 0) + 1,
        "tool_success": False,
        "tool_error": "",
        "decision_trace": state.get("decision_trace", []) + [
            {
                "step": "retry",
                "decision": (
                    f"Retrying tool execution "
                    f"(attempt {state.get('retry_count', 0) + 1})"
                )
            }
        ]
    }

def tool_failure_response(state: ServiceDeskState):

    return {
        "response": (
            "I was unable to complete the requested action "
            "after multiple attempts.\n\n"
            f"Tool: {state['tool_name']}\n"
            f"Error: {state['tool_error']}\n\n"
            "No further action was taken."
        )
    }

def create_audit_entry(
    state: ServiceDeskState,
    action: str
):
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_request": state.get("user_input", ""),
        "tool": state.get("tool_name", ""),
        "ticket_id": state.get("ticket_id", ""),
        "action": action,
        "success": state.get("tool_success", False),
        "retry_count": state.get("retry_count", 0),
        "error_type": (
            state.get("tool_error_type", "")
        )
    }
def audit_tool_action(state: ServiceDeskState):

    if state["tool_success"]:

        action = "Tool execution successful"

    else:

        action = "Tool execution failed"

    entry = create_audit_entry(
        state,
        action
    )

    history = state.get("audit_log", [])

    return {
        "audit_log": history + [entry]
    }

def add_decision_trace(
    state: ServiceDeskState,
    step: str,
    decision: str
):

    trace = state.get("decision_trace", [])

    entry = {
        "step": step,
        "decision": decision
    }

    return {
        "decision_trace": trace + [entry]
    }

def route_after_classification(state: ServiceDeskState):

    if state["next_action"] == "escalate":
        return "escalate"

    return "self_service"

def route_after_tool_decision(state: ServiceDeskState):
    if state["tool_name"] == "create_service_ticket":
        return "check_duplicate_ticket"

    if state["tool_name"] == "check_ticket_status":
        return "resolve_ticket_reference"

    if state["tool_name"] == "update_ticket_status":
        return "resolve_ticket_reference"

    if state["tool_required"]:
        return "execute_tool"

    return "route_issue"

def route_after_ticket_resolution(state: ServiceDeskState):

    if state["tool_name"] == "update_ticket_status":
        return "validate_status"

    if state["ticket_id"]:
        return "execute_tool"

    return "end"

def route_after_approval(state: ServiceDeskState):

    if state["approval_status"] == "approved":
        return "approved"

    return "rejected"

def route_after_duplicate_check(state: ServiceDeskState):

    if state["duplicate_ticket"]:
        return "duplicate"

    return "approval"

def route_after_status_validation(state: ServiceDeskState):

    if state["status_transition_valid"]:
        return "execute"

    return "end"

def route_after_tool_execution(state: ServiceDeskState):

    if state["tool_success"]:
        return "success"

    if state["retry_count"] < 2:
        return "retry"

    return "failure"

def route_after_audit(state: ServiceDeskState):

    if state["tool_success"]:
        return "success"
    if state["retry_count"] < 2:
        return "retry"

    return "failure"

graph = StateGraph(ServiceDeskState)

# Nodes
graph.add_node("classify_issue", classify_issue)
graph.add_node("route_issue", route_issue)
graph.add_node("escalate", escalation_response)
graph.add_node("self_service", self_service_response)
graph.add_node("retrieve_knowledge", retrieve_knowledge)
graph.add_node("decide_tool", decide_tool)
graph.add_node("resolve_ticket_reference",resolve_ticket_reference)
graph.add_node("execute_tool", execute_tool)
graph.add_node("tool_response", tool_response)
graph.add_node("check_duplicate_ticket",check_duplicate_ticket)
graph.add_node("duplicate_ticket_response",duplicate_ticket_response)
graph.add_node("request_approval",request_approval)
graph.add_node("request_ticket_clarification",request_ticket_clarification)
graph.add_node("validate_status_transition",validate_status_transition)
graph.add_node("prepare_tool_retry",prepare_tool_retry)
graph.add_node("tool_failure_response",tool_failure_response)
graph.add_node("audit_tool_action",audit_tool_action)

# Flow
graph.add_edge(START, "classify_issue")

graph.add_edge("classify_issue","retrieve_knowledge")

graph.add_edge("retrieve_knowledge", "decide_tool")

# Tool decision
graph.add_conditional_edges(
    "decide_tool",
    route_after_tool_decision,
    {   
        "check_duplicate_ticket": "check_duplicate_ticket",
        "request_approval": "request_approval",
        "resolve_ticket_reference": "resolve_ticket_reference",
        "execute_tool": "execute_tool",
        "route_issue": "route_issue"
    }
)

graph.add_conditional_edges(
    "check_duplicate_ticket",
    route_after_duplicate_check,
    {
        "duplicate": "duplicate_ticket_response",
        "approval": "request_approval"
    }
)

graph.add_conditional_edges(
    "request_approval",
    route_after_approval,
    {
        "approved": "execute_tool",
        "rejected": END
    }
)

graph.add_edge("duplicate_ticket_response", END)

#graph.add_edge("resolve_ticket_reference", "execute_tool")
graph.add_conditional_edges(
    "resolve_ticket_reference",
    route_after_ticket_resolution,
    {
        "validate_status": "validate_status_transition",
        "execute_tool": "execute_tool",
        "clarification": "request_ticket_clarification",
        "end": END
    }
)

graph.add_conditional_edges(
    "validate_status_transition",
    route_after_status_validation,
    {
        "execute": "execute_tool",
        "end": END
    }
)

graph.add_edge("request_ticket_clarification", "execute_tool")
graph.add_conditional_edges(
    "execute_tool",
    route_after_tool_execution,
    {
        "success": "audit_tool_action",
        "retry": "audit_tool_action",
        "failure": "audit_tool_action"
    }
)

graph.add_conditional_edges(
    "audit_tool_action",
    route_after_audit,
    {
        "success": "tool_response",
        "retry": "prepare_tool_retry",
        "failure": "tool_failure_response"
    }
)

graph.add_edge("prepare_tool_retry","execute_tool")
graph.add_edge("tool_failure_response",END)
graph.add_edge("tool_response", END)

# Priority routing for requests that don't need a tool
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

memory = MemorySaver()

app = graph.compile(checkpointer=memory)
