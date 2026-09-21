import shutil

import socket

import uuid

from servicenow_client import ServiceNowClient

servicenow = ServiceNowClient()


def create_service_ticket(
    issue: str,
    category: str,
    priority: str,
    issue_type: str
):
     return servicenow.create_incident(
        issue=issue,
        category=category,
        priority=priority
    )

def check_network_status():
    """
    Check basic network connectivity.
    """

    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)

        return {
            "status": "Connected",
            "message": "Network connectivity is available."
        }

    except OSError:
        return {
            "status": "Disconnected",
            "message": "Network connectivity could not be established."
        }

def check_disk_space():
    """
    Check available disk space on the machine.
    """
    try:
        print('Fetching space')
        total, used, free = shutil.disk_usage("C:\\")

        total_gb = total / (1024 ** 3)
        used_gb = used / (1024 ** 3)
        free_gb = free / (1024 ** 3)
        print(total_gb)
        print(used_gb)
        print(free_gb)
    except Exception as e:
         print(f"Exception{e}")

    return {
        "drive": "C:",
        "total_gb": round(total_gb, 2),
        "used_gb": round(used_gb, 2),
        "free_gb": round(free_gb, 2)
    }


if __name__ == "__main__":
    result = check_network_status()

    print("\nNetwork Status")
    print("=" * 40)
    print(f"Status    : {result['status']}")
    print(f"Message   : {result['message']}")

def check_ticket_status(ticket_id: str):

        return servicenow.get_incident(
        ticket_id=ticket_id
    )

def update_ticket_status(ticket_id: str, new_status: str):

    return servicenow.update_incident(
        ticket_id=ticket_id,
        status=new_status
    )