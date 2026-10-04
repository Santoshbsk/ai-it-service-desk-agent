from typing import TypedDict


class ServiceDeskState(TypedDict):
    user_input: str
    category: str
    priority: str
    response: str
    next_action: str
    retrieved_context: list
    tool_required: bool
    tool_name: str
    tool_result: dict
    approval_required: bool #If user confirmation is required for ticket creation
    approval_status: str #User confirmation for ticket creation
    ticket_id: str
    issue_type: str
    ticket_status: str
    ticket_history: list
    ticket_reference: str #Ticket reference provided by user to check status of a ticket
    clarification_required: bool #If multiple tickets are found and user needs to clarify which ticket they are referring to
    duplicate_ticket: bool
    duplicate_ticket_id: str
    requested_status: str
    status_transition_valid: bool #If ticket status transition is valid or not

    #Tool status related fields
    tool_success: bool
    tool_error: str
    retry_count: int
    tool_execution_time: float #Tool executin time

    #Audit log to keep track of all the actions taken by the agent
    audit_log: list
    tool_error_type: str

    #Decision trace to keep track of the reasoning behind each decision
    decision_trace: list

    classification_execution_time: float

    retrieval_execution_time: float

    response_generation_execution_time: float

    vector_search_execution_time: float
    
    reranking_execution_time: float