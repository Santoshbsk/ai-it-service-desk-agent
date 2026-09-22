from typing import TypedDict


class ServiceDeskState(TypedDict):
    user_input: str
    category: str
    priority: str
    response: str
    next_action: str
    retrieved_context: list