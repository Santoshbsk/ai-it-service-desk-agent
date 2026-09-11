from langchain_google_genai import ChatGoogleGenerativeAI
from state import ServiceDeskState
from config import GEMINI_API_KEY, LLM_MODEL


llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=0
)


def classify_issue(state: ServiceDeskState):

    prompt = f"""
You are an IT Service Desk AI Agent.

Classify the following employee IT issue.

Issue:
{state["user_input"]}

Choose exactly one category:
- Hardware
- Software
- Network
- Access
- Security
- Other

Also assign a priority:
- Low
- Medium
- High
- Critical

Return exactly in this format:

Category: <category>
Priority: <priority>
"""

    result = llm.invoke(prompt)

    # Gemini may return content as a list of content blocks
    if isinstance(result.content, list):
        text = "".join(
            block.get("text", "")
            if isinstance(block, dict)
            else str(block)
            for block in result.content
        )
    else:
        text = str(result.content)

    category = "Other"
    priority = "Medium"

    for line in text.splitlines():

        if line.startswith("Category:"):
            category = line.replace("Category:", "").strip()

        elif line.startswith("Priority:"):
            priority = line.replace("Priority:", "").strip()

    return {
        "category": category,
        "priority": priority
    }

def generate_response(state: ServiceDeskState):

    prompt = f"""
You are an enterprise IT Service Desk Agent.

Employee issue:
{state["user_input"]}

Category:
{state["category"]}

Priority:
{state["priority"]}

Provide a concise and professional response to the employee.

Do not pretend that you performed any technical action.
Simply acknowledge the issue and explain the next step.
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