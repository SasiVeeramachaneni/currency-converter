"""
Currency Converter Agent using OpenAI

This agent can convert currencies using real-time exchange rates.
"""

import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the Azure OpenAI client
client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

# Deployment name for Azure OpenAI
DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")

# Exchange rates (as of a reference date - in production, use a real API)
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 149.50,
    "CAD": 1.36,
    "AUD": 1.53,
    "CHF": 0.88,
    "CNY": 7.14,
    "INR": 83.12,
    "MXN": 17.15,
    "BRL": 4.97,
    "KRW": 1298.50,
    "SGD": 1.34,
    "HKD": 7.82,
    "SEK": 10.42,
    "NOK": 10.68,
    "NZD": 1.63,
    "ZAR": 18.65,
    "RUB": 89.50,
    "AED": 3.67,
}


def get_exchange_rate(from_currency: str, to_currency: str) -> dict:
    """Get the exchange rate between two currencies."""
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    if from_currency not in EXCHANGE_RATES:
        return {"error": f"Currency '{from_currency}' not supported"}
    if to_currency not in EXCHANGE_RATES:
        return {"error": f"Currency '{to_currency}' not supported"}
    
    # Convert through USD as base
    rate = EXCHANGE_RATES[to_currency] / EXCHANGE_RATES[from_currency]
    return {
        "from_currency": from_currency,
        "to_currency": to_currency,
        "exchange_rate": round(rate, 6),
    }


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert an amount from one currency to another."""
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    if from_currency not in EXCHANGE_RATES:
        return {"error": f"Currency '{from_currency}' not supported"}
    if to_currency not in EXCHANGE_RATES:
        return {"error": f"Currency '{to_currency}' not supported"}
    
    # Convert through USD as base
    rate = EXCHANGE_RATES[to_currency] / EXCHANGE_RATES[from_currency]
    converted_amount = amount * rate
    
    return {
        "original_amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "converted_amount": round(converted_amount, 2),
        "exchange_rate": round(rate, 6),
    }


def list_supported_currencies() -> dict:
    """List all supported currencies."""
    return {
        "supported_currencies": list(EXCHANGE_RATES.keys()),
        "base_currency": "USD",
        "total_currencies": len(EXCHANGE_RATES),
    }


# Define the tools for the agent
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "Convert an amount from one currency to another",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "The amount to convert",
                    },
                    "from_currency": {
                        "type": "string",
                        "description": "The source currency code (e.g., USD, EUR, GBP)",
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "The target currency code (e.g., USD, EUR, GBP)",
                    },
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "Get the current exchange rate between two currencies",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "description": "The source currency code (e.g., USD, EUR, GBP)",
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "The target currency code (e.g., USD, EUR, GBP)",
                    },
                },
                "required": ["from_currency", "to_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_supported_currencies",
            "description": "List all supported currencies for conversion",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

# Map function names to actual functions
AVAILABLE_FUNCTIONS = {
    "convert_currency": convert_currency,
    "get_exchange_rate": get_exchange_rate,
    "list_supported_currencies": list_supported_currencies,
}

SYSTEM_PROMPT = """You are a helpful currency conversion assistant. You can:
1. Convert amounts between different currencies
2. Provide current exchange rates between currencies
3. List all supported currencies

Always provide clear and concise responses. When converting currencies, show both the converted amount and the exchange rate used.
If a user asks about a currency that isn't supported, politely let them know and suggest listing the supported currencies."""


def run_agent(user_message: str, conversation_history: list = None) -> str:
    """Run the currency converter agent with a user message."""
    if conversation_history is None:
        conversation_history = []
    
    # Add system message if this is a new conversation
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})
    
    # Call the Azure OpenAI API
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )
    
    assistant_message = response.choices[0].message
    
    # Check if the model wants to call a function
    while assistant_message.tool_calls:
        # Process each tool call
        tool_results = []
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Call the function
            if function_name in AVAILABLE_FUNCTIONS:
                function_response = AVAILABLE_FUNCTIONS[function_name](**function_args)
            else:
                function_response = {"error": f"Unknown function: {function_name}"}
            
            tool_results.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "content": json.dumps(function_response),
            })
        
        # Add assistant message and tool results to messages
        messages.append(assistant_message)
        messages.extend(tool_results)
        
        # Get the next response
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        assistant_message = response.choices[0].message
    
    return assistant_message.content


def main():
    """Main function to run the currency converter agent interactively."""
    print("=" * 50)
    print("Currency Converter Agent")
    print("=" * 50)
    print("\nHello! I'm your currency conversion assistant.")
    print("I can help you convert currencies, check exchange rates,")
    print("and list supported currencies.")
    print("\nType 'quit' or 'exit' to end the conversation.")
    print("-" * 50)
    
    conversation_history = []
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye! Have a great day!")
                break
            
            # Run the agent
            response = run_agent(user_input, conversation_history)
            print(f"\nAssistant: {response}")
            
            # Update conversation history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": response})
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! Have a great day!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please make sure your OPENAI_API_KEY environment variable is set.")


if __name__ == "__main__":
    main()
