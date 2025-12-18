# Currency Converter Agent

An AI-powered currency conversion agent built with Azure OpenAI and exposed via the A2A (Agent-to-Agent) protocol for multi-agent collaboration.

## Overview

This project provides a currency converter agent that can:
- Convert amounts between different currencies
- Provide current exchange rates between currency pairs
- List all supported currencies

The agent is available in two modes:
1. **Standalone CLI** - Interactive command-line interface
2. **A2A Server** - Exposes the agent via the A2A protocol for other agents to discover and interact with

## Features

- **20 Supported Currencies**: USD, EUR, GBP, JPY, CAD, AUD, CHF, CNY, INR, MXN, BRL, KRW, SGD, HKD, SEK, NOK, NZD, ZAR, RUB, AED
- **Azure OpenAI Integration**: Uses Azure OpenAI for natural language understanding and function calling
- **A2A Protocol Compliance**: Enables multi-agent collaboration through standardized communication
- **Agent Card Discovery**: Other agents can discover capabilities via `/.well-known/agent-card.json`

## Prerequisites

- Python 3.11+
- Azure OpenAI account with API access
- API key and endpoint URL

## Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd currency-converter
   ```

2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and add your Azure OpenAI credentials:
   ```env
   AZURE_OPENAI_API_KEY=your-api-key-here
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
   AZURE_OPENAI_API_VERSION=2024-10-21
   ```

## Usage

### Option 1: Standalone CLI Mode

Run the interactive currency converter:

```bash
python3 main.py
```

Example interaction:
```
You: Convert 100 USD to EUR
Assistant: 100 USD converts to 92 EUR using an exchange rate of 1 USD = 0.92 EUR.

You: What currencies do you support?
Assistant: I support 20 currencies: USD, EUR, GBP, JPY, CAD, AUD, CHF, CNY, INR, MXN, BRL, KRW, SGD, HKD, SEK, NOK, NZD, ZAR, RUB, AED
```

Type `quit` or `exit` to end the session.

### Option 2: A2A Server Mode

Start the A2A-compliant server:

```bash
python3 a2a_server.py
```

The server will start at `http://localhost:8000` with:
- **Agent Card**: http://localhost:8000/.well-known/agent-card.json
- **A2A Endpoint**: http://localhost:8000/

#### Test with curl:

```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "1",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"text": "Convert 100 USD to EUR"}],
        "messageId": "msg-001"
      }
    }
  }'
```

#### View Agent Card:

```bash
curl http://localhost:8000/.well-known/agent-card.json
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key | Required |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Required |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Deployment name | `gpt-4o-mini` |
| `AZURE_OPENAI_API_VERSION` | API version | `2024-02-15-preview` |
| `A2A_HOST` | A2A server host | `0.0.0.0` |
| `A2A_PORT` | A2A server port | `8000` |

## Agent Capabilities

The A2A agent exposes three skills:

### 1. Currency Conversion
Convert amounts between currencies.

**Examples:**
- "Convert 100 USD to EUR"
- "How much is 50 GBP in JPY?"
- "Change 1000 INR to USD"

### 2. Exchange Rate Lookup
Get current exchange rates between currency pairs.

**Examples:**
- "What is the exchange rate from USD to EUR?"
- "EUR to GBP rate"
- "Show me the USD to INR exchange rate"

### 3. List Supported Currencies
View all available currencies.

**Examples:**
- "What currencies do you support?"
- "List all currencies"
- "Show supported currencies"

## Architecture

```
┌─────────────────────────────────────┐
│        User / Other Agents          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         A2A Protocol Layer          │
│   (Agent Card + JSON-RPC API)       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      Currency Converter Agent       │
│    (Azure OpenAI + Functions)       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     Currency Conversion Logic       │
│      (Exchange Rate Database)       │
└─────────────────────────────────────┘
```

## A2A Protocol Integration

This agent implements the [A2A Protocol](https://a2a-protocol.org) v3.1.1, enabling:

- **Discovery**: Other agents can find this agent via the agent card
- **Interoperability**: Standard communication protocol for agent-to-agent interaction
- **Message-Based Communication**: Uses Message objects (not Tasks) for responses
- **Multi-Agent Collaboration**: Can be orchestrated with other A2A-compliant agents

## AWS Deployment

For production deployment to AWS App Runner with AWS native authentication:

📖 **[AWS Deployment Guide](AWS_DEPLOYMENT.md)**

### Authentication Options:
- **API Gateway + Lambda Authorizer** - Full OAuth 2.0 / API key support
- **AWS WAF** - IP restrictions and rate limiting
- **VPC Private** - No public internet access

The deployment guide includes:
- Step-by-step AWS App Runner setup
- Three authentication strategies
- Environment variable configuration
- Monitoring and cost optimization

## Development

### Project Structure

```
currency-converter/
├── main.py                  # Standalone CLI interface
├── a2a_server.py            # A2A protocol server
├── test_message_output.py   # Test Message output format
├── test_comprehensive.py    # Comprehensive integration tests
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment configuration
├── .gitignore               # Git ignore rules
├── README.md                # This file
└── AWS_DEPLOYMENT.md        # AWS deployment guide
```

### Testing

Run the test suite to verify the agent is working correctly:

```bash
# Start the A2A server first
python3 a2a_server.py

# In another terminal, run tests
python3 test_message_output.py      # Test Message output format
python3 test_comprehensive.py       # Test all skills
```

The tests verify:
- ✅ Agent returns Message objects (not Task objects)
- ✅ Currency conversion works correctly
- ✅ Exchange rate lookup functions properly
- ✅ Currency listing returns all supported currencies

### Adding New Currency Pairs

Edit the `EXCHANGE_RATES` dictionary in both `main.py` and `a2a_server.py`:

```python
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    # Add more currencies here
}
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'uvicorn'"
Install dependencies for the correct Python version:
```bash
python3 -m pip install -r requirements.txt
```

### "Error code: 401 - Incorrect API key"
- Verify your Azure OpenAI credentials in `.env`
- Ensure you're using an Azure OpenAI key (not standard OpenAI)
- Check that the endpoint URL and deployment name are correct

### "Method Not Allowed" when accessing http://localhost:8000/
This is expected! The A2A protocol uses POST requests. Use the agent card endpoint or curl to test.

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

## Support

For issues or questions, please [open an issue](your-repo-url/issues).
