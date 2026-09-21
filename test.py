from servicenow_client import ServiceNowClient


client = ServiceNowClient()

result = client.create_incident(
    issue="Test incident created from AI IT Service Desk Agent",
    category="Software",
    priority="Medium"
)

print("\nServiceNow Response:")
print(result)