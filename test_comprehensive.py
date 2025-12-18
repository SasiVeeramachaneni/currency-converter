"""
Comprehensive test of the A2A Currency Converter Agent
"""

import requests
import json

def test_query(description, query):
    """Test a single query"""
    print(f"\n{'=' * 60}")
    print(f"Test: {description}")
    print(f"Query: {query}")
    print('=' * 60)
    
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"text": query}],
                "messageId": f"test-{hash(query) % 10000}"
            }
        },
        "id": 1
    }
    
    response = requests.post(
        "http://localhost:8000/",
        headers={"Content-Type": "application/json"},
        json=payload
    )
    
    result = response.json()
    
    if "result" in result and result["result"].get("kind") == "message":
        parts = result["result"].get("parts", [])
        for part in parts:
            if part.get("kind") == "text":
                print(f"✅ Response: {part.get('text')}")
        return True
    else:
        print(f"❌ Error: {result}")
        return False

# Run tests
print("=" * 60)
print("A2A Currency Converter Agent - Comprehensive Test")
print("=" * 60)

tests = [
    ("Currency Conversion", "Convert 100 USD to EUR"),
    ("Exchange Rate", "What is the exchange rate from GBP to JPY?"),
    ("List Currencies", "List all supported currencies"),
    ("Another Conversion", "How much is 500 CAD in INR?"),
    ("Different Format", "Change 1000 AUD to CHF"),
]

passed = 0
failed = 0

for description, query in tests:
    if test_query(description, query):
        passed += 1
    else:
        failed += 1

print(f"\n{'=' * 60}")
print(f"Test Results: {passed} passed, {failed} failed")
print(f"{'=' * 60}")
