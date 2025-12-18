"""
Currency Converter A2A Agent Server

This module exposes the currency converter agent via the A2A protocol,
allowing other agents to discover and interact with it.
"""

import os
import json
import asyncio
import uvicorn
from dotenv import load_dotenv
from openai import AzureOpenAI

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    Message,
    Part,
    Role,
    TaskState,
    TextPart,
)

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI client
azure_client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")

# Exchange rates
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


# OpenAI Tools definition
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


def run_openai_agent(user_message: str) -> str:
    """Run the currency converter agent with Azure OpenAI."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    response = azure_client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    assistant_message = response.choices[0].message

    # Process tool calls
    while assistant_message.tool_calls:
        tool_results = []
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            if function_name in AVAILABLE_FUNCTIONS:
                function_response = AVAILABLE_FUNCTIONS[function_name](**function_args)
            else:
                function_response = {"error": f"Unknown function: {function_name}"}

            tool_results.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "content": json.dumps(function_response),
            })

        messages.append(assistant_message)
        messages.extend(tool_results)

        response = azure_client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        assistant_message = response.choices[0].message

    return assistant_message.content


class CurrencyConverterExecutor(AgentExecutor):
    """A2A Agent Executor for the Currency Converter."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute the currency conversion request and return a Message."""
        try:
            # Get user input from the message
            user_input = context.get_user_input()

            # Run the OpenAI agent
            response_text = await asyncio.to_thread(run_openai_agent, user_input)

            # Create and send a Message response (not a Task)
            # Generate a unique message ID or use incoming message ID
            import uuid
            msg_id = f"response-{uuid.uuid4().hex[:8]}"
            
            response_message = Message(
                role=Role.agent,
                parts=[Part(root=TextPart(text=response_text))],
                message_id=msg_id,
            )
            
            await event_queue.enqueue_event(response_message)

        except Exception as e:
            # Create an error message response
            import uuid
            msg_id = f"error-{uuid.uuid4().hex[:8]}"
            
            error_message = Message(
                role=Role.agent,
                parts=[Part(root=TextPart(text=f"Error: {str(e)}"))],
                message_id=msg_id,
            )
            await event_queue.enqueue_event(error_message)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel operation - not applicable for simple message responses."""
        pass


def create_agent_card(host: str = "localhost", port: int = 8000) -> AgentCard:
    """Create the Agent Card for the Currency Converter agent."""
    # Use public URL from environment variable if available, otherwise construct from host:port
    public_url = os.environ.get("PUBLIC_URL", f"http://{host}:{port}")
    # Ensure URL ends with /
    if not public_url.endswith("/"):
        public_url += "/"
    
    return AgentCard(
        name="Currency Converter Agent",
        description="An AI-powered agent that converts currencies, provides exchange rates, and lists supported currencies. Supports 20 major world currencies.",
        url=public_url,
        version="1.0.0",
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=False,
            state_transition_history=False,
        ),
        skills=[
            AgentSkill(
                id="convert-currency",
                name="Currency Conversion",
                description="Convert an amount from one currency to another. Example: 'Convert 100 USD to EUR'",
                tags=["currency", "conversion", "finance", "money"],
                examples=[
                    "Convert 100 USD to EUR",
                    "How much is 50 GBP in JPY?",
                    "Change 1000 INR to USD",
                ],
            ),
            AgentSkill(
                id="exchange-rate",
                name="Exchange Rate Lookup",
                description="Get the current exchange rate between two currencies. Example: 'What is the exchange rate from USD to EUR?'",
                tags=["currency", "exchange-rate", "finance"],
                examples=[
                    "What is the exchange rate from USD to EUR?",
                    "EUR to GBP rate",
                    "Show me the USD to INR exchange rate",
                ],
            ),
            AgentSkill(
                id="list-currencies",
                name="List Supported Currencies",
                description="List all supported currencies for conversion.",
                tags=["currency", "list", "supported"],
                examples=[
                    "What currencies do you support?",
                    "List all currencies",
                    "Show supported currencies",
                ],
            ),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
    )


def create_a2a_app(host: str = "localhost", port: int = 8000):
    """Create the A2A Starlette application."""
    agent_card = create_agent_card(host, port)

    # Create the request handler with our executor
    request_handler = DefaultRequestHandler(
        agent_executor=CurrencyConverterExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # Create and return the A2A application
    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    return app.build()


def main():
    """Run the A2A server."""
    host = os.environ.get("A2A_HOST", "0.0.0.0")
    port = int(os.environ.get("A2A_PORT", "8000"))

    print("=" * 60)
    print("Currency Converter A2A Agent Server")
    print("=" * 60)
    print(f"\n🚀 Starting server at http://{host}:{port}")
    print(f"📋 Agent Card: http://{host}:{port}/.well-known/agent-card.json")
    print(f"🔗 A2A Endpoint: http://{host}:{port}/")
    print("\nSupported currencies:", ", ".join(EXCHANGE_RATES.keys()))
    print("-" * 60)

    app = create_a2a_app(host, port)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
