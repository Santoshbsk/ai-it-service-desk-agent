from typing import Literal

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

from state import ServiceDeskState
from config import GEMINI_API_KEY, LLM_MODEL


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
    ] = Field(description="The category of the IT issue")

    priority: Literal[
        "Low",
        "Medium",
        "High",
        "Critical"
    ] = Field(description="The priority of the IT issue")


classifier = llm.with_structured_output(IssueClassification)


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
        "priority": result.priority
    }


def route_issue(state: ServiceDeskState):

    if state["priority"] in ["High", "Critical"]:
        return {
            "next_action": "escalate"
        }

    return {
        "next_action": "self_service"
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

    prompt = f"""
You are an enterprise IT Service Desk Agent.

The employee reported:

{state["user_input"]}

Category: {state["category"]}
Priority: {state["priority"]}

This issue can initially be handled through self-service
troubleshooting.

Provide a concise response explaining that the next step
is to troubleshoot the issue.

Do NOT claim that any technical action has already been performed.
Do NOT claim that a ticket has been created.

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