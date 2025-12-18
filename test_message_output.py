"""
Test script to verify A2A agent returns Message (not Task)
"""

import requests
import json

# Test the agent card first
print("=" * 60)
print("Testing Agent Card")
print("=" * 60)
response = requests.get("http://localhost:8000/.well-known/agent-card.json")
agent_card = response.json()
print(f"Agent: {agent_card['name']}")
print(f"URL: {agent_card['url']}")
print(f"Skills: {len(agent_card['skills'])}")

# Test with a simple JSON-RPC request
print("\n" + "=" * 60)
print("Testing Message Output (Converting 100 USD to EUR)")
print("=" * 60)

# According to A2A protocol, we send a message and expect a message back
payload = {
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
        "message": {
            "role": "user",
            "parts": [{"text": "Convert 100 USD to EUR"}],
            "messageId": "test-msg-001"
        }
    },
    "id": 1
}

response = requests.post(
    "http://localhost:8000/",
    headers={"Content-Type": "application/json"},
    json=payload
)

print(f"Status Code: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}")

# Check if response contains a message (not a task)
result = response.json()
if "result" in result:
    print("\n✅ Received result field")
    result_data = result["result"]
    
    # Check the kind field
    if result_data.get("kind") == "message":
        print("✅ Result is a Message (not Task)")
        print(f"   Message ID: {result_data.get('messageId')}")
        print(f"   Role: {result_data.get('role')}")
        print(f"   Parts count: {len(result_data.get('parts', []))}")
        
        # Print the actual response text
        for part in result_data.get('parts', []):
            if part.get('kind') == 'text':
                print(f"   Response: {part.get('text')}")
    elif result_data.get("kind") == "task":
        print("❌ Result is a Task (should be Message)")
    else:
        print(f"⚠️  Unknown kind: {result_data.get('kind')}")
else:
    print(f"Response structure: {result.keys()}")
