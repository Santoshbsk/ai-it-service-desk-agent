# AI IT Service Desk Agent

An enterprise-style **Agentic AI IT Service Desk Agent** built with **Python, LangGraph, Gemini, RAG, and ServiceNow REST APIs**.

The agent can understand employee IT issues, retrieve relevant knowledge, reason about whether a tool is required, execute operational tools, interact with ServiceNow, request human approval for sensitive actions, prevent duplicate tickets, validate ticket lifecycle transitions, retry failed operations, and maintain audit and decision-trace information.

---

## 1. Project Overview

Traditional IT service desk chatbots generally follow predefined conversational flows.

This project implements a more agentic architecture:

```text
Employee
   │
   ▼
AI IT Service Desk Agent
   │
   ├── Understand & classify issue
   │
   ├── Retrieve relevant IT knowledge
   │
   ├── Decide whether a tool is required
   │
   ├── Execute tools when appropriate
   │
   ├── Apply deterministic safety controls
   │
   ├── Request human approval when required
   │
   ├── Interact with ServiceNow
   │
   ├── Validate ticket lifecycle
   │
   ├── Retry failed operations
   │
   ├── Record audit information
   │
   └── Return response
```

The project demonstrates a hybrid architecture where:

**LLM reasoning + deterministic guardrails + human-in-the-loop + enterprise tools**

work together rather than relying solely on an LLM.

---

# 2. Key Capabilities

The agent currently supports:

* IT issue classification
* Priority classification
* Knowledge-base retrieval using RAG
* RAG reranking
* Self-service troubleshooting
* High-priority escalation
* LLM-based tool selection
* Disk-space diagnostics
* Network connectivity diagnostics
* ServiceNow incident creation
* ServiceNow ticket status lookup
* ServiceNow ticket status updates
* Human approval before ticket creation
* Ticket reference resolution
* Duplicate-ticket prevention
* Ticket lifecycle validation
* Bounded tool retries
* Controlled failure handling
* Audit logging
* Decision tracing
* Configuration validation
* ServiceNow API error normalization
* Agent behavior evaluation

---

# 3. Technology Stack

| Technology          | Purpose                                  |
| ------------------- | ---------------------------------------- |
| Python              | Application development                  |
| LangGraph           | Agent orchestration and state management |
| LangChain           | LLM and retrieval integration            |
| Gemini              | Classification, reasoning and generation |
| Gemini Embeddings   | Knowledge-base embeddings                |
| ChromaDB            | Vector database                          |
| RAG                 | Enterprise IT knowledge retrieval        |
| RAGAS               | RAG evaluation                           |
| ServiceNow REST API | Enterprise ticket management             |
| Pydantic            | Structured LLM outputs                   |
| python-dotenv       | Environment configuration                |
| Requests            | ServiceNow API communication             |

---

# 4. Project Architecture

```text
                         ┌──────────────────────┐
                         │      Employee        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Classify Issue     │
                         │ Category / Type /    │
                         │ Priority             │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Retrieve KB        │
                         │ Chroma + Embeddings  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Decide Tool        │
                         │   LLM Reasoning      │
                         └──────────┬───────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     │                             │
                 Tool required                 No tool
                     │                             │
                     ▼                             ▼
             ┌────────────────┐          ┌────────────────┐
             │ Duplicate      │          │ Route Issue    │
             │ Check          │          └───────┬────────┘
             └───────┬────────┘                  │
                     │                   ┌────────┴────────┐
                     │                   │                 │
                 Duplicate           Self-Service      Escalate
                     │                   │                 │
                     ▼                   ▼                 ▼
                  Block              RAG Answer      Escalation
                                         
                     │
                No duplicate
                     │
                     ▼
             ┌────────────────┐
             │ Human Approval │
             └───────┬────────┘
                     │
                Approved
                     │
                     ▼
             ┌────────────────┐
             │ Execute Tool   │
             └───────┬────────┘
                     │
              ┌──────┴──────┐
              │             │
           Success        Failure
              │             │
              ▼             ▼
          Audit Log      Retry ≤ 2
              │             │
              ▼             ▼
           Response     Controlled
                        Failure
```

---

# 5. LangGraph State

The agent uses a shared state object to coordinate information between nodes.

```python
class ServiceDeskState(TypedDict):
    user_input: str

    category: str
    issue_type: str
    priority: str

    response: str
    next_action: str
    retrieved_context: list

    tool_required: bool
    tool_name: str
    tool_result: dict

    approval_required: bool
    approval_status: str

    ticket_id: str
    ticket_status: str
    ticket_history: list

    ticket_reference: str
    clarification_required: bool

    duplicate_ticket: bool
    duplicate_ticket_id: str

    requested_status: str
    status_transition_valid: bool

    tool_success: bool
    tool_error: str
    tool_error_type: str
    retry_count: int

    audit_log: list
    decision_trace: list
```

This allows the graph to maintain context throughout the complete interaction.

---

# Streamlit Web Interface

The project includes a Streamlit chat interface in `streamlit_app.py` for
interacting with the AI IT Service Desk Agent through a browser.

The interface provides:

* A welcome message and conversational chat history
* IT troubleshooting and knowledge-base responses
* Issue category, type, and priority details
* Ticket information, decision traces, and audit logs
* Human approval before creating a ServiceNow ticket
* Resume support for ticket approval and ticket-ID clarification prompts

## Start the Streamlit App

From the project directory, activate the virtual environment and start
Streamlit:

### Windows PowerShell

```powershell
.\rag-env\Scripts\Activate.ps1
streamlit run streamlit_app.py
```

### Other environments

```bash
streamlit run streamlit_app.py
```

Streamlit opens the application in a browser, usually at
`http://localhost:8501`.

The Streamlit app uses a stable LangGraph thread ID to preserve the current
conversation, ticket history, and interrupted approval workflow during the
session. When the agent asks for approval or clarification, enter the answer
in the chat input to resume the paused workflow.

---

# 6. Issue Classification

The agent uses structured LLM output to classify an IT issue into:

### Category

* Hardware
* Software
* Network
* Access
* Security
* Other

### Issue Type

* VPN
* Laptop Performance
* Password Reset
* Software Installation
* Email
* Other

### Priority

* Low
* Medium
* High
* Critical

The classification output is represented using Pydantic structured output rather than relying on free-form LLM responses.

Example:

```text
User:
"My VPN is not connecting."

Classification:

Category    : Network
Issue Type  : VPN
Priority    : Medium
```

---

# 7. Knowledge Retrieval / RAG

The agent uses a local IT knowledge base containing troubleshooting documentation.

Current knowledge documents:

```text
knowledge_base/
├── vpn_troubleshooting.txt
├── laptop_performance.txt
├── password_reset.txt
├── software_installation.txt
└── email_troubleshooting.txt
```

The documents are embedded using Gemini embeddings and stored in ChromaDB.

Retrieval flow:

```text
User Query
    │
    ▼
Gemini Embedding
    │
    ▼
ChromaDB Similarity Search
    │
    ▼
Top 5 Documents
    │
    ▼
Gemini Reranking
    │
    ▼
Top 3 Relevant Documents
    │
    ▼
Grounded Response
```

The response-generation prompt instructs the model to:

* Use only retrieved knowledge
* Avoid inventing troubleshooting steps
* Avoid claiming actions were already performed
* Provide numbered troubleshooting steps
* Include source documents
* State when the knowledge base is insufficient

---

# 8. RAG Evaluation

The RAG pipeline was evaluated using RAGAS.

Current curated evaluation results:

| Metric            |  Score |
| ----------------- | -----: |
| Context Precision | 1.0000 |
| Context Recall    | 0.9750 |
| Faithfulness      | 0.9661 |
| Answer Relevancy  | 0.7646 |

The evaluation dataset includes questions covering:

* VPN troubleshooting
* Laptop performance
* Password reset
* MFA
* Email troubleshooting
* Software installation
* Multi-document scenarios
* Out-of-scope questions

The RAG evaluation is separate from the agent behavior evaluation.

---

# 9. Agentic Tool Selection

The agent uses structured LLM output to determine whether an operational tool is required.

Available tools:

```text
check_disk_space
check_network_status
create_service_ticket
check_ticket_status
update_ticket_status
none
```

The agent is explicitly instructed not to execute a tool merely because the issue belongs to that tool's domain.

For example:

```text
"My VPN is not working."
```

results in:

```text
Tool: none
```

Whereas:

```text
"Please check my network connection."
```

results in:

```text
Tool: check_network_status
```

And:

```text
"Please raise a service ticket for my VPN issue."
```

results in:

```text
Tool: create_service_ticket
```

This separates:

**Problem understanding**

from

**authorization to perform an operational action.**

---

# 10. Available Tools

## Disk Space

Uses Python's `shutil.disk_usage()` to inspect the local C: drive.

Returns:

```text
Drive
Total space
Used space
Free space
```

---

## Network Status

Uses a controlled connectivity check to determine whether network connectivity is available.

Returns:

```text
Connected
```

or

```text
Disconnected
```

---

# 11. ServiceNow Integration

The project integrates with a personal ServiceNow Developer instance using the ServiceNow Table REST API.

Supported operations:

```text
Create Incident
       │
       ▼
Get Incident
       │
       ▼
Update Incident
```

The ServiceNow integration is abstracted behind:

```python
ServiceNowClient
```

This keeps enterprise-system-specific API logic separate from the agent orchestration layer.

---

# 12. ServiceNow Ticket Creation

When the user explicitly requests ticket creation:

```text
Employee
   ↓
Classify
   ↓
Tool Decision
   ↓
Duplicate Check
   ↓
Human Approval
   ↓
ServiceNow
   ↓
Incident Created
```

The ServiceNow incident includes information such as:

```text
Short Description
Description
Category
Priority
```

The ServiceNow incident number is returned to the agent.

Example:

```text
INC0012345
```

---

# 13. Human-in-the-Loop

Ticket creation is protected by a human approval step.

Before creating a ticket, the agent interrupts execution and asks:

```text
APPROVAL REQUIRED

The agent is requesting permission to create an IT service ticket.

Category : Network
Priority : High
Issue    : VPN is not connecting

Do you want to create this ticket?
Reply with: yes or no
```

The graph resumes using LangGraph's interrupt/resume mechanism.

```text
Agent
  │
  ▼
Approval Required
  │
  ├── Yes ──► Create Ticket
  │
  └── No  ──► Stop
```

This prevents an autonomous agent from creating operational tickets without explicit user approval.

---

# 14. Ticket Reference Resolution

The agent can resolve references such as:

```text
INC0012345
```

or natural-language references such as:

```text
my latest ticket
my VPN ticket
the password ticket
```

The resolver uses deterministic matching against ticket history.

If multiple tickets match, the agent requests clarification rather than guessing.

Example:

```text
I found multiple tickets that may match your request:

1. INC0012345 - VPN is not connecting
2. INC0012346 - VPN keeps disconnecting

Please provide the ticket ID you want me to check.
```

---

# 15. Duplicate Ticket Prevention

The agent prevents duplicate active

## Agent Evaluation

The AI IT Service Desk Agent includes a deterministic evaluation suite covering
core agentic behaviors, safety controls, and operational reliability.

### Evaluation Results

| Capability | Test Cases | Result |
|---|---:|---:|
| Classification accuracy | 3 | 3/3 |
| Tool selection accuracy | 11 | 11/11 |
| Routing accuracy | 4 | 4/4 |
| Duplicate ticket prevention | 3 | 3/3 |
| Ticket lifecycle validation | 6 | 6/6 |
| Human-in-the-loop approval | 4 | 4/4 |
| Retry & failure handling | 4 | 4/4 |
| Audit logging | 3 | 3/3 |
| **Total** | **38** | **38/38 (100%)** |

### Evaluation Coverage

The evaluation suite validates the following agent behaviors:

- **Issue classification**
  - Category classification
  - Issue-type classification

- **Tool selection**
  - Disk-space checks
  - Network checks
  - ServiceNow ticket creation
  - Ticket status lookup
  - Ticket status updates
  - Avoiding unnecessary tool execution

- **Decision routing**
  - Self-service for lower-priority issues
  - Escalation for high/critical-priority issues

- **Duplicate prevention**
  - Prevents duplicate active tickets for the same issue type
  - Allows new tickets after previous tickets are resolved
  - Allows tickets for different issue types

- **Ticket lifecycle validation**
  - Created → In Progress
  - In Progress → Resolved
  - Resolved → Closed
  - Blocks invalid state transitions

- **Human-in-the-loop**
  - Requires user approval before ticket creation
  - Handles approval and rejection

- **Reliability**
  - Bounded retries
  - Maximum of three tool execution attempts
  - Controlled failure after retry exhaustion

- **Auditability**
  - Records tool execution outcomes
  - Records retry information
  - Records ticket references
  - Records normalized error types

### Agent Safety Controls

The evaluation also validates an important tool-use safety principle:

> The agent should not execute an operational tool merely because the user's
> issue is related to that tool.

For example:

```text
"My VPN is not working."
        ↓
No explicit tool request
        ↓
No tool execution