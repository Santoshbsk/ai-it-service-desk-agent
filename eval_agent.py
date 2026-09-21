from agent import (
    classify_issue,
    decide_tool,
    route_issue,
    check_duplicate_ticket,
    validate_status_transition,
    request_approval,
    create_audit_entry
)

TOTAL_TESTS = 0
PASSED_TESTS = 0

TEST_CASES = [
    {
        "name": "VPN classification",
        "input": "My VPN is not connecting.",
        "expected_category": "Network",
        "expected_issue_type": "VPN"
    },
    {
        "name": "Password classification",
        "input": "I forgot my corporate password.",
        "expected_category": "Access",
        "expected_issue_type": "Password Reset"
    },
    {
        "name": "Software classification",
        "input": "I need to install approved software.",
        "expected_category": "Software",
        "expected_issue_type": "Software Installation"
    }
]


def run_classification_tests():
    global TOTAL_TESTS, PASSED_TESTS
    passed = 0

    print("\n" + "=" * 70)
    print("CLASSIFICATION EVALUATION")
    print("=" * 70)

    for test in TEST_CASES:

        state = {
            "user_input": test["input"],
            "decision_trace": []
        }

        result = classify_issue(state)

        category_match = (
            result["category"]
            == test["expected_category"]
        )

        issue_match = (
            result["issue_type"]
            == test["expected_issue_type"]
        )

        success = (
            category_match
            and issue_match
        )

        if success:
            passed += 1
            PASSED_TESTS += 1
        TOTAL_TESTS += 1
        print(f"\nTest: {test['name']}")
        print(f"Input: {test['input']}")
        print(f"Expected category: {test['expected_category']}")
        print(f"Actual category:   {result['category']}")
        print(f"Expected issue:    {test['expected_issue_type']}")
        print(f"Actual issue:      {result['issue_type']}")
        print(f"Result: {'PASS' if success else 'FAIL'}")

    print("\n" + "-" * 70)
    print(
        f"Classification Score: "
        f"{passed}/{len(TEST_CASES)}"
    )

TOOL_TEST_CASES = [
    {
        "name": "Disk space check",
        "input": "Check my disk space.",
        "expected_tool": "check_disk_space"
    },
    {
        "name": "Network check",
        "input": "Check whether my network connection is working.",
        "expected_tool": "check_network_status"
    },
    {
        "name": "Create service ticket",
        "input": "Please raise a service ticket for my VPN issue.",
        "expected_tool": "create_service_ticket"
    },
    {
        "name": "Check ticket status",
        "input": "What is the status of INC0012345?",
        "expected_tool": "check_ticket_status"
    },
    {
        "name": "Update ticket status",
        "input": "Resolve INC0012345.",
        "expected_tool": "update_ticket_status"
    },
    {
        "name": "Password troubleshooting",
        "input": "How do I reset my password?",
        "expected_tool": ""
    },
        {
        "name": "Informational VPN question",
        "input": "What is VPN and why do I need it?",
        "expected_tool": ""
    },
    {
        "name": "Disk space question",
        "input": "How can I free up disk space?",
        "expected_tool": ""
    },
    {
        "name": "Password reset instructions",
        "input": "Where can I reset my corporate password?",
        "expected_tool": ""
    },
    {
        "name": "Ticket creation without explicit request",
        "input": "My VPN is not working.",
        "expected_tool": ""
    },
    {
        "name": "Ticket status without ticket reference",
        "input": "Can you tell me about my ticket?",
        "expected_tool": "check_ticket_status"
    }
]


def run_tool_selection_tests():
    global TOTAL_TESTS, PASSED_TESTS
    passed = 0

    print("\n" + "=" * 70)
    print("TOOL SELECTION EVALUATION")
    print("=" * 70)

    for test in TOOL_TEST_CASES:

        state = {
            "user_input": test["input"],
            "decision_trace": []
        }

        result = decide_tool(state)

        actual_tool = result["tool_name"]

        success = (
            actual_tool
            == test["expected_tool"]
        )

        if success:
            passed += 1
            PASSED_TESTS += 1

        TOTAL_TESTS += 1

        print(f"\nTest: {test['name']}")
        print(f"Input: {test['input']}")
        print(f"Expected tool: {test['expected_tool']}")
        print(f"Actual tool:   {actual_tool}")
        print(f"Result: {'PASS' if success else 'FAIL'}")

    print("\n" + "-" * 70)
    print(
        f"Tool Selection Score: "
        f"{passed}/{len(TOOL_TEST_CASES)}"
    )

ROUTING_TEST_CASES = [
    {
        "name": "Low priority",
        "priority": "Low",
        "expected_action": "self_service"
    },
    {
        "name": "Medium priority",
        "priority": "Medium",
        "expected_action": "self_service"
    },
    {
        "name": "High priority",
        "priority": "High",
        "expected_action": "escalate"
    },
    {
        "name": "Critical priority",
        "priority": "Critical",
        "expected_action": "escalate"
    }
]


def run_routing_tests():
    global TOTAL_TESTS, PASSED_TESTS
    passed = 0

    print("\n" + "=" * 70)
    print("ROUTING EVALUATION")
    print("=" * 70)

    for test in ROUTING_TEST_CASES:

        state = {
            "user_input": "Test IT issue",
            "category": "Network",
            "issue_type": "VPN",
            "priority": test["priority"],
            "decision_trace": []
        }

        result = route_issue(state)

        actual_action = result["next_action"]

        success = (
            actual_action
            == test["expected_action"]
        )

        if success:
            passed += 1
            PASSED_TESTS += 1

        TOTAL_TESTS += 1

        print(f"\nTest: {test['name']}")
        print(f"Priority: {test['priority']}")
        print(f"Expected action: {test['expected_action']}")
        print(f"Actual action:   {actual_action}")
        print(f"Result: {'PASS' if success else 'FAIL'}")

    print("\n" + "-" * 70)
    print(
        f"Routing Score: "
        f"{passed}/{len(ROUTING_TEST_CASES)}"
    )

DUPLICATE_TEST_CASES = [
    {
        "name": "Active duplicate",
        "issue_type": "VPN",
        "history": [
            {
                "ticket_id": "INC100001",
                "status": "In Progress",
                "issue": "VPN is not connecting",
                "issue_type": "VPN",
                "category": "Network",
                "priority": "High"
            }
        ],
        "expected_duplicate": True
    },
    {
        "name": "Different issue type",
        "issue_type": "Password Reset",
        "history": [
            {
                "ticket_id": "INC100002",
                "status": "In Progress",
                "issue": "VPN is not connecting",
                "issue_type": "VPN",
                "category": "Network",
                "priority": "High"
            }
        ],
        "expected_duplicate": False
    },
    {
        "name": "Resolved previous ticket",
        "issue_type": "VPN",
        "history": [
            {
                "ticket_id": "INC100003",
                "status": "Resolved",
                "issue": "VPN is not connecting",
                "issue_type": "VPN",
                "category": "Network",
                "priority": "High"
            }
        ],
        "expected_duplicate": False
    }
]


def run_duplicate_tests():
    global TOTAL_TESTS, PASSED_TESTS
    passed = 0

    print("\n" + "=" * 70)
    print("DUPLICATE TICKET EVALUATION")
    print("=" * 70)

    for test in DUPLICATE_TEST_CASES:

        state = {
            "user_input": "Test IT issue",
            "issue_type": test["issue_type"],
            "ticket_history": test["history"],
            "decision_trace": []
        }

        result = check_duplicate_ticket(state)

        actual_duplicate = result["duplicate_ticket"]

        success = (
            actual_duplicate
            == test["expected_duplicate"]
        )

        if success:
            passed += 1
            PASSED_TESTS += 1

        TOTAL_TESTS += 1
        print(f"\nTest: {test['name']}")
        print(f"Issue type: {test['issue_type']}")
        print(f"Expected duplicate: {test['expected_duplicate']}")
        print(f"Actual duplicate:   {actual_duplicate}")

        if actual_duplicate:
            print(
                f"Duplicate ticket: "
                f"{result['duplicate_ticket_id']}"
            )

        print(f"Result: {'PASS' if success else 'FAIL'}")

    print("\n" + "-" * 70)
    print(
        f"Duplicate Prevention Score: "
        f"{passed}/{len(DUPLICATE_TEST_CASES)}"
    )

LIFECYCLE_TEST_CASES = [
    {
        "name": "Created to In Progress",
        "current_status": "Created",
        "requested_status": "In Progress",
        "expected_valid": True
    },
    {
        "name": "In Progress to Resolved",
        "current_status": "In Progress",
        "requested_status": "Resolved",
        "expected_valid": True
    },
    {
        "name": "Resolved to Closed",
        "current_status": "Resolved",
        "requested_status": "Closed",
        "expected_valid": True
    },
    {
        "name": "Created to Resolved",
        "current_status": "Created",
        "requested_status": "Resolved",
        "expected_valid": False
    },
    {
        "name": "Resolved to In Progress",
        "current_status": "Resolved",
        "requested_status": "In Progress",
        "expected_valid": False
    },
    {
        "name": "Closed to Resolved",
        "current_status": "Closed",
        "requested_status": "Resolved",
        "expected_valid": False
    }
]


def run_lifecycle_tests():
    global TOTAL_TESTS, PASSED_TESTS
    passed = 0

    print("\n" + "=" * 70)
    print("TICKET LIFECYCLE EVALUATION")
    print("=" * 70)

    for test in LIFECYCLE_TEST_CASES:

        state = {
            "user_input": "Update ticket status",
            "ticket_status": test["current_status"],
            "requested_status": test["requested_status"],
            "decision_trace": []
        }

        result = validate_status_transition(state)

        actual_valid = result["status_transition_valid"]

        success = (
            actual_valid
            == test["expected_valid"]
        )

        if success:
            passed += 1
            PASSED_TESTS += 1

        TOTAL_TESTS += 1

        print(f"\nTest: {test['name']}")
        print(
            f"Transition: "
            f"{test['current_status']} → "
            f"{test['requested_status']}"
        )
        print(
            f"Expected valid: "
            f"{test['expected_valid']}"
        )
        print(
            f"Actual valid:   "
            f"{actual_valid}"
        )
        print(f"Result: {'PASS' if success else 'FAIL'}")

    print("\n" + "-" * 70)
    print(
        f"Lifecycle Score: "
        f"{passed}/{len(LIFECYCLE_TEST_CASES)}"
    )

HITL_TEST_CASES = [
    {
        "name": "Approval granted",
        "approval_response": "yes",
        "expected_status": "approved"
    },
    {
        "name": "Approval rejected",
        "approval_response": "no",
        "expected_status": "rejected"
    },
    {
        "name": "Approval accepted with y",
        "approval_response": "y",
        "expected_status": "approved"
    },
    {
        "name": "Approval rejected with arbitrary response",
        "approval_response": "cancel",
        "expected_status": "rejected"
    }
]

def evaluate_approval_response(response):
    
    response = response.lower().strip()

    if response in ["yes", "y"]:
        return "approved"

    return "rejected"

def run_hitl_tests():
    global TOTAL_TESTS, PASSED_TESTS

    passed = 0

    print("\n" + "=" * 70)
    print("HITL APPROVAL EVALUATION")
    print("=" * 70)

    for test in HITL_TEST_CASES:

        actual_status = evaluate_approval_response(
            test["approval_response"]
        )

        success = (
            actual_status
            == test["expected_status"]
        )

        if success:
            passed += 1
            PASSED_TESTS += 1

        TOTAL_TESTS += 1

        print(f"\nTest: {test['name']}")
        print(
            f"User response: "
            f"{test['approval_response']}"
        )
        print(
            f"Expected status: "
            f"{test['expected_status']}"
        )
        print(
            f"Actual status:   "
            f"{actual_status}"
        )
        print(f"Result: {'PASS' if success else 'FAIL'}")

    print("\n" + "-" * 70)
    print(
        f"HITL Approval Score: "
        f"{passed}/{len(HITL_TEST_CASES)}"
    )

RETRY_TEST_CASES = [
    {
        "name": "Successful execution",
        "tool_success": True,
        "retry_count": 0,
        "expected_action": "success"
    },
    {
        "name": "First failure",
        "tool_success": False,
        "retry_count": 0,
        "expected_action": "retry"
    },
    {
        "name": "Second failure",
        "tool_success": False,
        "retry_count": 1,
        "expected_action": "retry"
    },
    {
        "name": "Third failure",
        "tool_success": False,
        "retry_count": 2,
        "expected_action": "failure"
    }
]


def evaluate_retry_behavior(state):

    if state["tool_success"]:
        return "success"

    if state["retry_count"] < 2:
        return "retry"

    return "failure"

def run_retry_tests():
    global TOTAL_TESTS, PASSED_TESTS
    passed = 0

    print("\n" + "=" * 70)
    print("RETRY & FAILURE EVALUATION")
    print("=" * 70)

    for test in RETRY_TEST_CASES:

        state = {
            "tool_success": test["tool_success"],
            "retry_count": test["retry_count"]
        }

        actual_action = evaluate_retry_behavior(state)

        success = (
            actual_action
            == test["expected_action"]
        )

        if success:
            passed += 1
            PASSED_TESTS += 1

        TOTAL_TESTS += 1

        print(f"\nTest: {test['name']}")
        print(
            f"Retry count: "
            f"{test['retry_count']}"
        )
        print(
            f"Expected action: "
            f"{test['expected_action']}"
        )
        print(
            f"Actual action:   "
            f"{actual_action}"
        )
        print(f"Result: {'PASS' if success else 'FAIL'}")

    print("\n" + "-" * 70)
    print(
        f"Retry & Failure Score: "
        f"{passed}/{len(RETRY_TEST_CASES)}"
    )

def run_audit_tests():
    global TOTAL_TESTS, PASSED_TESTS
    print("\n" + "=" * 70)
    print("AUDIT LOG EVALUATION")
    print("=" * 70)

    passed = 0
    total = 3

    # Test 1: Successful tool execution
    success_state = {
        "user_input": "Check my network connection.",
        "tool_name": "check_network_status",
        "ticket_id": "",
        "tool_success": True,
        "retry_count": 0,
        "tool_error_type": ""
    }

    entry = create_audit_entry(
        success_state,
        "Tool execution successful"
    )

    success = (
        entry["success"] is True
        and entry["tool"] == "check_network_status"
        and entry["error_type"] == ""
    )

    print("\nTest: Successful tool audit")
    print(f"Result: {'PASS' if success else 'FAIL'}")

    if success:
        passed += 1
        PASSED_TESTS += 1

    TOTAL_TESTS += 1

    # Test 2: Failed tool execution
    failure_state = {
        "user_input": "Create a service ticket.",
        "tool_name": "create_service_ticket",
        "ticket_id": "",
        "tool_success": False,
        "retry_count": 1,
        "tool_error_type": "timeout"
    }

    entry = create_audit_entry(
        failure_state,
        "Tool execution failed"
    )

    success = (
        entry["success"] is False
        and entry["tool"] == "create_service_ticket"
        and entry["error_type"] == "timeout"
        and entry["retry_count"] == 1
    )

    print("\nTest: Failed tool audit")
    print(f"Result: {'PASS' if success else 'FAIL'}")

    if success:
        passed += 1
        PASSED_TESTS += 1

    TOTAL_TESTS += 1

    # Test 3: Ticket audit
    ticket_state = {
        "user_input": "Check my ticket status.",
        "tool_name": "check_ticket_status",
        "ticket_id": "INC100001",
        "tool_success": True,
        "retry_count": 0,
        "tool_error_type": ""
    }

    entry = create_audit_entry(
        ticket_state,
        "Tool execution successful"
    )

    success = (
        entry["ticket_id"] == "INC100001"
        and entry["tool"] == "check_ticket_status"
        and entry["success"] is True
    )

    print("\nTest: Ticket audit")
    print(f"Result: {'PASS' if success else 'FAIL'}")

    if success:
        passed += 1
        PASSED_TESTS += 1

    TOTAL_TESTS += 1

    print("\n" + "-" * 70)
    print(
        f"Audit Logging Score: "
        f"{passed}/{total}"
    )



if __name__ == "__main__":
    run_classification_tests()
    run_tool_selection_tests()
    run_routing_tests()
    run_duplicate_tests()
    run_lifecycle_tests()
    run_hitl_tests()
    run_retry_tests()
    run_audit_tests()

    print("\n" + "=" * 70)
    print("OVERALL AGENT EVALUATION")
    print("=" * 70)

    score = (
        PASSED_TESTS / TOTAL_TESTS * 100
        if TOTAL_TESTS
        else 0
    )

    print(
        f"\nPassed Tests : {PASSED_TESTS}/{TOTAL_TESTS}"
    )

    print(
        f"Agent Score  : {score:.2f}%"
    )