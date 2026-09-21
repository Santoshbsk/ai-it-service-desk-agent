import streamlit as st

from agent import app
from langgraph.types import Command


st.set_page_config(
    page_title="AI IT Service Desk Agent",
    page_icon="🤖",
    layout="wide"
)


st.title("🤖 AI IT Service Desk Agent")
st.caption(
    "Enterprise Agentic AI for IT troubleshooting, "
    "ticket management and ServiceNow integration"
)


# ---------------------------------------------------------
# Session State
# ---------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Welcome to the AI IT Service Desk.\n\n"
                "I can help troubleshoot IT issues, check your device or "
                "network, and create or manage ServiceNow tickets.\n\n"
                "How can I help you today?"
            )
        }
    ]

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "streamlit-service-desk-001"

if "first_request" not in st.session_state:
    st.session_state.first_request = True

if "pending_interrupt" not in st.session_state:
    st.session_state.pending_interrupt = False


# ---------------------------------------------------------
# Display Previous Messages
# ---------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ---------------------------------------------------------
# User Input
# ---------------------------------------------------------

user_input = st.chat_input(
    "Describe your IT issue..."
)


if user_input:

    # Display user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    with st.chat_message("user"):
        st.markdown(user_input)


    # Initial agent state
    initial_state = {
        "user_input": user_input,

        "category": "",
        "issue_type": "",
        "priority": "",

        "response": "",
        "next_action": "",
        "retrieved_context": [],

        "tool_required": False,
        "tool_name": "",
        "tool_result": {},

        "approval_required": False,
        "approval_status": "",

        "ticket_id": "",
        "ticket_status": "",
        "ticket_history": [],

        "ticket_reference": "",
        "clarification_required": False,

        "duplicate_ticket": False,
        "duplicate_ticket_id": "",

        "requested_status": "",
        "status_transition_valid": False,

        "tool_success": True,
        "tool_error": "",
        "tool_error_type": "",
        "retry_count": 0,

        "audit_log": [],
        "decision_trace": []
    }


    config = {
        "configurable": {
            "thread_id": st.session_state.thread_id
        }
    }


    # Run agent
    with st.chat_message("assistant"):

        with st.spinner("AI Service Desk Agent is working..."):
            if st.session_state.pending_interrupt:

                result = app.invoke(
                    Command(resume=user_input),
                    config=config
                )

            elif st.session_state.first_request:

                result = app.invoke(
                    initial_state,
                    config=config
                )

                st.session_state.first_request = False

            else:

                result = app.invoke(
                    {"user_input": user_input},
                    config=config
                )


        # -------------------------------------------------
        # Handle Interrupt
        # -------------------------------------------------

        if "__interrupt__" in result:

            interrupt_data = result["__interrupt__"][0]

            st.warning(interrupt_data.value)

            st.session_state.pending_interrupt = True

            st.stop()

        st.session_state.pending_interrupt = False


        # -------------------------------------------------
        # Display Response
        # -------------------------------------------------

        response = result.get(
            "response",
            "I was unable to generate a response."
        )

        st.markdown(response)


        # -------------------------------------------------
        # Agent Details
        # -------------------------------------------------

        with st.expander("🔍 Agent Details"):

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(
                    "**Category:**",
                    result.get("category", "")
                )

            with col2:
                st.write(
                    "**Issue Type:**",
                    result.get("issue_type", "")
                )

            with col3:
                st.write(
                    "**Priority:**",
                    result.get("priority", "")
                )


        # -------------------------------------------------
        # Ticket Information
        # -------------------------------------------------

        if result.get("ticket_id"):

            with st.expander("🎫 Ticket Information"):

                st.write(
                    "**Ticket ID:**",
                    result["ticket_id"]
                )

                st.write(
                    "**Status:**",
                    result.get("ticket_status", "")
                )


        # -------------------------------------------------
        # Decision Trace
        # -------------------------------------------------

        if result.get("decision_trace"):

            with st.expander("🧠 Decision Trace"):

                for trace in result["decision_trace"]:

                    st.write(
                        f"**{trace['step']}** → "
                        f"{trace['decision']}"
                    )


        # -------------------------------------------------
        # Audit Log
        # -------------------------------------------------

        if result.get("audit_log"):

            with st.expander("📋 Audit Log"):

                st.json(
                    result["audit_log"]
                )


        # Save assistant response
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response
            }
        )