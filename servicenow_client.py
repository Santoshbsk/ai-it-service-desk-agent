from config import (
    SERVICENOW_URL,
    SERVICENOW_USERNAME,
    SERVICENOW_PASSWORD
)

import requests


class ServiceNowClient:

    def __init__(self):

        self.base_url = SERVICENOW_URL
        self.username = SERVICENOW_USERNAME
        self.password = SERVICENOW_PASSWORD

        self.tickets = {}

    def _map_servicenow_state(self, state: str):

        mapping = {
            "1": "In Progress",
            "2": "In Progress",
            "6": "Resolved",
            "7": "Closed"
        }

        return mapping.get(state, state)

    def _map_status_to_servicenow_state(
    self,
    status: str
    ):
        mapping = {
            "Created": "1",
            "In Progress": "2",
            "Resolved": "6",
            "Closed": "7"
        }

        return mapping.get(status, "1")

    def create_incident(
    self,
    issue: str,
    category: str,
    priority: str
    ):
        url = f"{self.base_url}/api/now/table/incident"

        payload = {
            "short_description": issue,
            "description": issue,
            "category": category,
            "priority": self._map_priority(priority)
        }
        try:
            response = requests.post(
            url,
            auth=(
                self.username,
                self.password
            ),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=(10, 60)
        )
        except requests.exceptions.Timeout:
            return {
                "error": "ServiceNow request timed out.",
                "error_type": "timeout"
            }

        except requests.exceptions.ConnectionError:
            return {
                "error": "Unable to connect to ServiceNow.",
                "error_type": "connection"
            }

        if not response.ok:
            return self._handle_response_error(response)

        data = response.json()["result"]

        return {
            "ticket_id": data["number"],
            "sys_id": data["sys_id"],
            "status": "Created",
            "issue": issue,
            "category": category,
            "priority": priority,
            "message": "ServiceNow incident created successfully."
        }
    def _map_priority(self, priority: str):
        mapping = {
            "Critical": "1",
            "High": "2",
            "Medium": "3",
            "Low": "4"
        }

        return mapping.get(priority, "3")

    def get_incident(self, ticket_id: str):

        url = f"{self.base_url}/api/now/table/incident"

        params = {
            "sysparm_query": f"number={ticket_id}",
            "sysparm_limit": 1,
            "sysparm_fields": (
                "sys_id,number,short_description,"
                "description,category,priority,state"
            )
        }

        try:
            response = requests.get(
                url,
                auth=(
                    self.username,
                    self.password
                ),
                headers={
                    "Accept": "application/json"
                },
                params=params,
                timeout=(10, 60)
            )

        except requests.exceptions.Timeout:
            return {
                "error": "ServiceNow request timed out.",
                "error_type": "timeout"
            }

        except requests.exceptions.ConnectionError:
            return {
                "error": "Unable to connect to ServiceNow.",
                "error_type": "connection"
            }

        if not response.ok:
            return self._handle_response_error(response)

        results = response.json().get("result", [])

        if not results:
            return {
                "error": f"Ticket {ticket_id} was not found."
            }

        incident = results[0]

        return {
            "ticket_id": incident["number"],
            "sys_id": incident["sys_id"],
            "status": self._map_servicenow_state(
                incident.get("state", "")
            ),
            "issue": incident.get("short_description", ""),
            "description": incident.get("description", ""),
            "category": incident.get("category", ""),
            "priority": incident.get("priority", ""),
            "message": "ServiceNow incident retrieved successfully."
        }

    
    def update_incident(
    self,
    ticket_id: str,
    status: str
    ):
        # First find the incident and its sys_id
        incident = self.get_incident(ticket_id)

        if "error" in incident:
            return incident

        sys_id = incident["sys_id"]

        url = (
            f"{self.base_url}/api/now/table/incident/"
            f"{sys_id}"
        )

        payload = {
            "state": self._map_status_to_servicenow_state(status)
        }

        try:
            response = requests.patch(
                url,
                auth=(
                    self.username,
                    self.password
                ),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=(10, 60)
            )

        except requests.exceptions.Timeout:
            return {
                "error": "ServiceNow request timed out.",
                "error_type": "timeout"
            }

        except requests.exceptions.ConnectionError:
            return {
                "error": "Unable to connect to ServiceNow.",
                "error_type": "connection"
            }

        if not response.ok:
            return self._handle_response_error(response)
        data = response.json()["result"]

        return {
            "ticket_id": data["number"],
            "sys_id": data["sys_id"],
            "status": self._map_servicenow_state(
                data.get("state", "")
            ),
            "issue": data.get("short_description", ""),
            "category": data.get("category", ""),
            "priority": data.get("priority", ""),
            "message": (
                f"ServiceNow incident {ticket_id} "
                f"updated successfully."
            )
        }

def _handle_response_error(
    self,
    response
):
    if response.status_code == 401:
        return {
            "error": "ServiceNow authentication failed.",
            "error_type": "authentication"
        }

    if response.status_code == 403:
        return {
            "error": "ServiceNow access was denied.",
            "error_type": "authorization"
        }

    if response.status_code == 404:
        return {
            "error": "The requested ServiceNow record was not found.",
            "error_type": "not_found"
        }

    if response.status_code == 429:
        return {
            "error": "ServiceNow rate limit was reached.",
            "error_type": "rate_limit"
        }

    if 500 <= response.status_code < 600:
        return {
            "error": "ServiceNow is temporarily unavailable.",
            "error_type": "server_error"
        }

    return {
        "error": "ServiceNow request failed.",
        "error_type": "api_error"
    }