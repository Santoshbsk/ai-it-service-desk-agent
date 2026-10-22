import streamlit as st
import uuid
import time

from agent import app
from langgraph.types import Command




st.set_page_config(
    page_title="AI IT Service Desk Agent",
    page_icon="🤖",
    layout="wide"
)
st.markdown("""
<style>

[data-testid="stSidebar"] {
    font-size: 13px;
}

[data-testid="stSidebar"] p {
    font-size: 13px;
}

[data-testid="stSidebar"] label {
    font-size: 13px;
}

[data-testid="stSidebar"] .stMarkdown {
    font-size: 13px;
}
[data-testid="stMarkdownContainer"]{
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)


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
    st.session_state.thread_id = (
        f"streamlit-service-desk-{uuid.uuid4()}"
    )

if "first_request" not in st.session_state:
    st.session_state.first_request = True

if "pending_interrupt" not in st.session_state:
    st.session_state.pending_interrupt = False

if "observability_history" not in st.session_state:
    st.session_state.observability_history = []


def reset_conversation():
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
    st.session_state.thread_id = (
        f"streamlit-service-desk-{uuid.uuid4()}"
    )
    st.session_state.first_request = True
    st.session_state.pending_interrupt = False
    st.session_state.observability_history = []


with st.sidebar:
    st.subheader("Conversation")
    if st.button("Reset conversation", use_container_width=True):
        reset_conversation()
        st.rerun()

    st.divider()

    st.subheader("📊 Session Metrics")

    history = st.session_state.observability_history

    if history:

        total_requests = len(history)

        successful_tools = sum(
            1
            for item in history
            if item["tool_success"]
            and item["tool"] != "none"
        )

        total_retries = sum(
            item["retry_count"]
            for item in history
        )

        average_response_time = (
            sum(item["response_time"] for item in history)
            / total_requests
        )

        st.metric(
            "Requests",
            total_requests
        )

        st.metric(
            "Successful Tools",
            successful_tools
        )

        st.metric(
            "Total Retries",
            total_retries
        )

        st.metric(
            "Avg Response Time",
            f"{average_response_time:.2f}s"
        )

        st.subheader("🔧 Tool Performance")

        tool_stats = {}

        for item in st.session_state.observability_history:

            tool_name = item.get("tool_name")

            if not tool_name:
                continue

            if tool_name not in tool_stats:
                tool_stats[tool_name] = {
                    "executions": 0,
                    "total_time": 0,
                    "successful": 0
                }

            tool_stats[tool_name]["executions"] += 1

            tool_stats[tool_name]["total_time"] += item.get(
                "tool_execution_time", 0
            )

            if item.get("tool_success"):
                tool_stats[tool_name]["successful"] += 1


        for tool_name, stats in tool_stats.items():

            executions = stats["executions"]
            total_time = stats["total_time"]
            successful = stats["successful"]

            average_time = total_time / executions

            success_rate = (
                successful / executions
            ) * 100

            st.write(f"### 🔹 {tool_name}")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Executions",
                    executions
                )

            with col2:
                st.metric(
                    "Average Time",
                    f"{average_time * 1000:.2f} ms"
                )

            with col3:
                st.metric(
                    "Success Rate",
                    f"{success_rate:.0f}%"
                )
        st.subheader("📈 Response Latency Trend")

        if st.session_state.observability_history:

            latency_data = []

            for i, item in enumerate(
                st.session_state.observability_history,
                start=1
            ):
                latency_data.append({
                    "Request": i,
                    "Response Time (ms)": item.get(
                        "response_time", 0
                    )*1000
                })

            st.line_chart(
                latency_data,
                x="Request",
                y="Response Time (ms)"
            )

        else:

            st.info("No execution history available yet.")
    else:

        st.caption("No executions recorded yet.")

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
        "decision_trace": [],
        "classification_execution_time": 0.0,
        "retrieval_execution_time": 0.0,
        "response_generation_execution_time": 0.0,
        "vector_search_execution_time": 0.0,
        "reranking_execution_time": 0.0,
        "tool_execution_time": 0.0,
        "conversation_history": []
    }


    config = {
        "configurable": {
            "thread_id": st.session_state.thread_id
        }
    }


    # Run agent
    with st.chat_message("assistant"):

        with st.spinner("AI Service Desk Agent is working..."):

            start_time = time.perf_counter()

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
                     {
                        "user_input": user_input,
                        "classification_execution_time": 0.0,
                        "retrieval_execution_time": 0.0,
                        "response_generation_execution_time": 0.0,
                        "vector_search_execution_time": 0.0,
                        "reranking_execution_time": 0.0,
                        "tool_execution_time": 0.0,
                    },
                    config=config
                )

            end_time = time.perf_counter()

            execution_time = end_time - start_time
            # -------------------------------------------------
# Store Observability History
# -------------------------------------------------

            st.session_state.observability_history.append(
                {
                    "category": result.get("category", ""),
                    "issue_type": result.get("issue_type", ""),
                    "tool": result.get("tool_name", "none"),
                   # "tool_success": result.get("tool_success", False),
                    "retry_count": result.get("retry_count", 0),
                    "response_time": execution_time,
                    "audit_events": len(
                        result.get("audit_log", [])
                    ),
                    "tool_name": result.get("tool_name", ""),
                    "tool_execution_time": result.get("tool_execution_time", 0),
                    "tool_success": result.get("tool_success", False),
                    "classification_execution_time": result.get("classification_execution_time", 0),
                    "retrieval_execution_time": result.get("retrieval_execution_time", 0),
                    "response_generation_execution_time": result.get("response_generation_execution_time", 0),
                    "vector_search_execution_time": result.get("vector_search_execution_time", 0),
                    "reranking_execution_time": result.get("reranking_execution_time", 0),
                    "other_execution_time": max(
                    0,
                    execution_time
                    - result.get("classification_execution_time", 0)
                    - result.get("retrieval_execution_time", 0)
                    - result.get("response_generation_execution_time", 0)
                    )
                    
                }
            )
    

        # -------------------------------------------------
        # Handle Interrupt
        # -------------------------------------------------

        if "__interrupt__" in result:

            interrupt_data = result["__interrupt__"][0]

            interrupt_message = str(interrupt_data.value)

            st.warning(interrupt_message)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"⚠️ {interrupt_message}"
                }
            )

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

        # -------------------------------------------------
# Agent Observability
# -------------------------------------------------

        with st.expander("🔍 Agent Observability"):

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Category",
                    result.get("category", "N/A")
                )

            with col2:
                st.metric(
                    "Issue Type",
                    result.get("issue_type", "N/A")
                )

            with col3:
                st.metric(
                    "Priority",
                    result.get("priority", "N/A")
                )

            with col4:
                tool_name = result.get("tool_name", "none")

                st.metric(
                    "Tool",
                    tool_name
                )

            st.divider()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Tool Required**")
                st.write(
                    "Yes" if result.get("tool_required") else "No"
                )

            with col2:
                st.write("**Tool Success**")
                st.write(
                    "Yes" if result.get("tool_success") else "No"
                )

            with col3:
                st.write("**Retry Count**")
                st.write(
                    result.get("retry_count", 0)
                )
            
            # Tool result
            if result.get("tool_result"):

                st.subheader("🔧 Tool Result")

                st.json(
                    result["tool_result"]
                )

            # Tool error
            if result.get("tool_error"):

                st.subheader("⚠️ Tool Error")

                st.error(
                    result["tool_error"]
                )

                        # -------------------------------------------------
            # Execution Metrics
            # -------------------------------------------------

            st.subheader("📊 Execution Metrics")

            decision_trace = result.get("decision_trace", [])
            audit_log = result.get("audit_log", [])
            
            tool_execution_count = sum(
                1
                for trace in decision_trace
                if trace.get("step") == "execute_tool"
            )

            retry_count = result.get("retry_count", 0)

            tool_success = result.get("tool_success", False)

            tool_execution_time = result.get("tool_execution_time",0)

            classification_execution_time = result.get("classification_execution_time", 0)

            retrieval_execution_time = result.get("retrieval_execution_time", 0)

            response_generation_execution_time = result.get("response_generation_execution_time", 0)

            audit_count = len(audit_log)

            vector_search_execution_time = result.get( "vector_search_execution_time", 0)

            reranking_execution_time = result.get("reranking_execution_time", 0)



            col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11 = st.columns(11)

            with col1:
                st.metric(
                    "Tool Executions",
                    tool_execution_count
                )

            with col2:
                st.metric(
                    "Retries",
                    retry_count
                )

            with col3:
                st.metric(
                    "Tool Status",
                    "Success" if tool_success else "Failed"
                )

            with col4:
                st.metric(
                    "Audit Events",
                    audit_count
                )

            with col5:
                st.metric(
                    "Response Time",
                    f"{execution_time:.2f} sec"
                )
            
            with col6:
                st.metric(
                    "Tool Time",
                    f"{tool_execution_time* 1000:.2f}ms"
                )

            with col7:
                st.metric(
                    "Classification Time",
                    f"{classification_execution_time:.2f}s"
                )

            with col8:
                st.metric(
                    "Retrieval Time",
                    f"{retrieval_execution_time * 1000:.2f} ms"
                )

            with col9:
                st.metric(
                    "Response Generation Time",
                    f"{response_generation_execution_time * 1000:.2f} ms"
                )

            with col10:
                st.metric(
                    "Vector Search Time",
                    f"{vector_search_execution_time * 1000:.2f} ms"
                )

            with col11:
                st.metric(
                    "Reranking Time",
                    f"{reranking_execution_time * 1000:.2f} ms"
                )

            st.subheader("Latency Breakdown")
            other_time = max(
                0,
                execution_time
                - result.get("classification_execution_time", 0)
                - result.get("retrieval_execution_time", 0)
                - result.get("response_generation_execution_time", 0)
                - result.get("tool_execution_time", 0)
            )

            #print(f"Tool Execution Time { result.get("tool_execution_time", 0) }")
            latency_data = {
                "Classification": (
                    result.get("classification_execution_time", 0) * 1000
                ),
                "Vector Search": (
                    result.get("vector_search_execution_time", 0) * 1000
                ),
                "Reranking": (
                    result.get("reranking_execution_time", 0) * 1000
                ),
                "Response Generation": (
                    result.get("response_generation_execution_time", 0) * 1000
                ),
                "Tool Execution": (
                    result.get("tool_execution_time", 0) * 1000
                ),
                "Other / Orchestration": (
                    other_time * 1000
                ),
            }

            st.bar_chart(latency_data)

            total_latency = execution_time

            if total_latency > 0:
                latency_percent = {
                    "Classification": (
                        result.get("classification_execution_time", 0)
                        / total_latency * 100
                    ),
                    "Vector Search": (
                        result.get("vector_search_execution_time", 0)
                        / total_latency * 100
                    ),
                    "Reranking": (
                        result.get("reranking_execution_time", 0)
                        / total_latency * 100
                    ),
                    "Response Generation": (
                        result.get("response_generation_execution_time", 0)
                        / total_latency * 100
                    ),
                    "Tool Execution": (
                        result.get("tool_execution_time", 0)
                        / total_latency * 100
                    ),
                    "Other / Orchestration": (
                        other_time / total_latency * 100
                    ),
                }

                st.subheader("Latency Contribution (%)")
                st.bar_chart(latency_percent)
            # -------------------------------------------------
            # Request Summary
            # -------------------------------------------------

            st.subheader("📋 Request Summary")

            tool_name = result.get("tool_name", "none")
            tool_required = result.get("tool_required", False)

            if tool_required:
                execution_path = "Tool Execution"
            elif result.get("retrieved_context"):
                execution_path = "RAG / Knowledge Retrieval"
            else:
                execution_path = "Direct Response"

            summary_col1, summary_col2 = st.columns(2)

            with summary_col1:
                st.write("**Execution Path**")
                st.write(execution_path)

                st.write("**Category**")
                st.write(result.get("category", "N/A"))

                st.write("**Issue Type**")
                st.write(result.get("issue_type", "N/A"))

                st.write("**Tool**")
                st.write(tool_name)

            with summary_col2:
                st.write("**Total Latency**")
                st.write(f"{execution_time:.2f} sec")

                st.write("**Tools Executed**")
                st.write(tool_execution_count)

                st.write("**Retries**")
                st.write(retry_count)

                st.write("**Audit Events**")
                st.write(audit_count)

            st.write("**Major Latency Contributors**")

            latency_contributors = {
                "Classification": classification_execution_time,
                "Vector Search": vector_search_execution_time,
                "Reranking": reranking_execution_time,
                "Response Generation": response_generation_execution_time,
                "Tool Execution": tool_execution_time,
                "Other / Orchestration": other_time,
            }

            latency_contributors = {
                name: value
                for name, value in latency_contributors.items()
                if value > 0
            }

            for name, value in sorted(
                latency_contributors.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                percentage = (
                    value / execution_time * 100
                    if execution_time > 0
                    else 0
                )

                st.write(
                    f"**{name}** — "
                    f"{value * 1000:.2f} ms "
                    f"({percentage:.1f}%)"
                )
            # Decision trace
            if result.get("decision_trace"):

                st.subheader("🧠 Decision Trace")

                for index, trace in enumerate(
                    result["decision_trace"],
                    start=1
                ):
                    step = trace.get("step", "")
                    decision = trace.get("decision", "")

                    if step == "execute_tool":
                        st.write(
                            f"{index}. 🔧 {step} → {decision} "
                            f"({tool_execution_time*1000:.2f}ms)"
                        )
                    else:
                        st.write(
                            f"{index}. {step} → {decision}"
                        )
                    # st.write(
                    #     f"**{index}. {trace['step']}** → "
                    #     f"{trace['decision']}"
                    # )

            st.subheader("🔄 Agent Execution Flow")

            flow_steps = result.get("decision_trace", [])

            if flow_steps:

                for index, trace in enumerate(flow_steps):

                    step = trace.get("step", "Unknown")
                    decision = trace.get("decision", "")

                    st.markdown(
                        f"**{index + 1}. {step}**"
                    )

                    if decision:
                        st.caption(decision)

                    if index < len(flow_steps) - 1:
                        st.markdown("↓")

            else:

                st.caption("No execution trace available.")

            # Audit log
            if result.get("audit_log"):

                st.subheader("📋 Audit Log")

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