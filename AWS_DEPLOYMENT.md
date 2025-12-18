# AWS App Runner Deployment Guide

This guide walks you through deploying the Currency Converter A2A Agent to AWS App Runner and securing it with AWS native services.

## Prerequisites

- AWS Account with appropriate permissions
- GitHub account
- Azure OpenAI API credentials
- AWS CLI installed (optional)

## Authentication Options

You have **three AWS-native options** for securing your agent:

### Option 1: AWS API Gateway + Lambda Authorizer (Recommended)
- Best for production
- Full OAuth 2.0 support
- Custom authorization logic
- Rate limiting & throttling
- Request/response transformation

### Option 2: AWS WAF (Web Application Firewall)
- IP-based restrictions
- Geographic blocking
- Rate limiting
- Bot protection
- Good for basic security

### Option 3: VPC + Private Link
- Private deployment
- No public internet access
- Access via VPC peering or PrivateLink
- Most secure option

## Deployment Steps

### Step 1: Push Code to GitHub
## Deployment Steps

### Step 1: Push Code to GitHub

```bash
git init
git add .
git commit -m "Initial commit - Currency Converter A2A Agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 2: Deploy to AWS App Runner

1. **Go to AWS Console:**
   - Navigate to AWS App Runner: https://console.aws.amazon.com/apprunner/

2. **Click "Create service"**

3. **Configure Source:**
   - **Repository type**: Source code repository
   - **Connect to GitHub**: Click "Add new" and authorize AWS
   - **Repository**: Select your `currency-converter` repository
   - **Branch**: `main`
   - **Deployment trigger**: Automatic

4. **Configure Build:**
   - **Configuration file**: Use a configuration file
   - **Configuration file location**: `apprunner.yaml`

5. **Configure Service:**
   - **Service name**: `currency-converter-agent`
   - **Virtual CPU**: 1 vCPU
   - **Memory**: 2 GB
   - **Environment variables**:
     
     | Name | Value |
     |------|-------|
     | `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key |
     | `AZURE_OPENAI_ENDPOINT` | Your Azure endpoint URL |
     | `AZURE_OPENAI_DEPLOYMENT_NAME` | Your deployment (e.g., `gpt-4o`) |
     | `AZURE_OPENAI_API_VERSION` | `2024-10-21` |
     | `PORT` | `8000` |

6. **Auto Scaling:**
   - Min instances: 1
   - Max instances: 5
   - Max concurrency: 100

7. **Health Check:**
   - Path: `/.well-known/agent-card.json`
   - Interval: 10 seconds

8. **Create & Deploy** (takes 3-5 minutes)

Your service URL will be: `https://xxxxx.us-east-1.awsapprunner.com`

---

## Security Configuration

Choose one of the following options:

## 🔐 Option 1: API Gateway + Lambda Authorizer (RECOMMENDED)

This provides full OAuth 2.0 / API Key authentication.

### Step 1: Create Lambda Authorizer

1. **Create Lambda function** (Python 3.11):

```python
import json

def lambda_handler(event, context):
    """
    Lambda authorizer for API Gateway
    Validates API key or OAuth token
    """
    token = event.get('authorizationToken', '')
    
    # Remove 'Bearer ' prefix if present
    if token.startswith('Bearer '):
        token = token[7:]
    
    # Validate against your API key (store in AWS Secrets Manager in production)
    # For demo: you can hardcode or fetch from Secrets Manager
    valid_api_key = "your-secret-api-key"  # Replace with actual validation
    
    if token == valid_api_key:
        return generate_policy('user', 'Allow', event['methodArn'])
    else:
        return generate_policy('user', 'Deny', event['methodArn'])

def generate_policy(principal_id, effect, resource):
    auth_response = {
        'principalId': principal_id
    }
    
    if effect and resource:
        policy_document = {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        }
        auth_response['policyDocument'] = policy_document
    
    return auth_response
```

2. **Deploy the Lambda function**

### Step 2: Create API Gateway

1. **Create REST API:**
   - Go to API Gateway console
   - Create API → REST API
   - Name: `currency-converter-api`

2. **Create Authorizer:**
   - Authorizers → Create New Authorizer
   - Name: `currency-converter-auth`
   - Type: Lambda
   - Lambda Function: Select your authorizer function
   - Token Source: `Authorization`
   - Authorization Caching: Enabled (300 seconds)

3. **Create Resource & Method:**
   - Resources → Create Resource → "Proxy resource"
   - Resource path: `/{proxy+}`
   - Enable CORS: Yes
   
4. **Configure Integration:**
   - Integration type: HTTP Proxy
   - HTTP method: ANY
   - Endpoint URL: `https://YOUR-APP-RUNNER-URL/{proxy}`
   - Add `Authorization` to Method Request
   - Set Authorizer to your Lambda authorizer

5. **Deploy API:**
   - Actions → Deploy API
   - Stage: `prod`
   - Get your invoke URL: `https://xxxxx.execute-api.us-east-1.amazonaws.com/prod`

### Step 3: Test

```bash
# Without token (should fail)
curl https://YOUR-API-GATEWAY-URL/

# With token (should work)
curl -H "Authorization: Bearer your-secret-api-key" \
  https://YOUR-API-GATEWAY-URL/.well-known/agent-card.json
```

---

## 🔐 Option 2: AWS WAF (IP & Rate Limiting)

Simpler option for IP-based restrictions.

### Step 1: Create WAF Web ACL

1. **Go to AWS WAF console**
2. **Create web ACL:**
   - Name: `currency-converter-waf`
   - Resource type: Regional resources (App Runner)
   - Region: Your App Runner region
   - Associated AWS resources: Select your App Runner service

3. **Add Rules:**

   **Rule 1: IP Allow List**
   - Rule type: IP set
   - Action: Allow
   - Add your allowed IP addresses

   **Rule 2: Rate Limiting**
   - Rule type: Rate-based rule
   - Rate limit: 1000 requests per 5 minutes
   - Action: Block

   **Rule 3: Geo Blocking (Optional)**
   - Rule type: Geo match
   - Countries to block: Select countries
   - Action: Block

4. **Default action:** Block (only allow rules pass)

5. **Create web ACL**

### Step 2: Test

```bash
# From allowed IP
curl https://YOUR-APP-RUNNER-URL/.well-known/agent-card.json

# From blocked IP (will get 403)
```

---

## 🔐 Option 3: VPC + Private Deployment

Most secure - no public access.

### Step 1: Configure App Runner VPC

1. **App Runner console** → Your service → Configuration → Networking
2. **Enable VPC connector:**
   - Create new VPC connector
   - Select your VPC
   - Select private subnets
   - Select security groups

### Step 2: Access via VPC

Access your agent only from within your VPC using:
- VPC peering
- AWS PrivateLink
- VPN connection
- Direct Connect

---

## Cost Comparison

| Option | Setup Complexity | Monthly Cost* | Best For |
|--------|-----------------|--------------|----------|
| **API Gateway + Lambda** | Medium | $3-10 | Production APIs with OAuth |
| **AWS WAF** | Low | $5-15 | IP restrictions, rate limiting |
| **VPC Private** | High | $0-5 | Internal/private deployments |

*Estimated additional costs beyond App Runner

---

## Monitoring

### CloudWatch Logs

App Runner automatically sends logs to CloudWatch:
- Log group: `/aws/apprunner/YOUR-SERVICE-NAME`
- View: CloudWatch Console → Logs → Log groups

### CloudWatch Metrics

Monitor these metrics:
- `2xxStatusCount` - Successful requests
- `4xxStatusCount` - Client errors  
- `5xxStatusCount` - Server errors
- `RequestCount` - Total requests
- `Latency` - Response time

### Set Up Alarms

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name currency-converter-high-errors \
  --alarm-description "Alert on high 5xx errors" \
  --metric-name 5xxStatusCount \
  --namespace AWS/AppRunner \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

---

## Updating Your Service

### Automatic Updates (Recommended)
Push to GitHub → App Runner auto-deploys

### Manual Deployment
App Runner console → Deploy → Deploy latest commit

---

## Best Practices

---

## Best Practices

1. **Use AWS Secrets Manager** for sensitive credentials
2. **Enable CloudWatch alarms** for error rates
3. **Set up API Gateway** for production workloads
4. **Use AWS WAF** for DDoS protection
5. **Enable HTTPS** (App Runner provides by default)
6. **Monitor costs** with AWS Cost Explorer
7. **Set up auto-scaling** based on traffic patterns

## Example Client Usage

Once deployed with API Gateway:

```python
from a2a.client import ClientFactory

# Connect to your agent via API Gateway
client = await ClientFactory.connect(
    "https://YOUR-API-GATEWAY-URL",
    interceptors=[
        lambda request: request.headers.update({
            "Authorization": "Bearer your-api-key"
        })
    ]
)

response = await client.send_message("Convert 100 USD to EUR")
print(response)
```

## Troubleshooting

### Service fails to start
- Check CloudWatch logs
- Verify environment variables
- Test Azure OpenAI credentials locally

### 403 Forbidden
- Check API Gateway authorizer
- Verify API key/token
- Check WAF rules

### High latency
- Check Azure OpenAI quotas
- Increase App Runner CPU/memory
- Review CloudWatch metrics

## Cleanup

Delete resources to avoid charges:
1. App Runner service
2. API Gateway (if created)
3. Lambda functions
4. WAF Web ACL
5. CloudWatch log groups (optional)

## Cost Estimates

### App Runner
- 1 vCPU, 2GB: ~$25-35/month
- With auto-scaling (2-5 instances): ~$50-100/month

### Additional Services
- API Gateway: $3.50/million requests + $0.09/GB data
- WAF: $5/month + $1/million requests
- Lambda: Negligible for authorizer

Total monthly cost: **$30-120** depending on traffic

## Next Steps

- [ ] Deploy to App Runner
- [ ] Choose authentication option
- [ ] Set up monitoring
- [ ] Configure custom domain
- [ ] Test with A2A clients
- [ ] Set up CI/CD pipeline

## Support Resources

- [AWS App Runner Docs](https://docs.aws.amazon.com/apprunner/)
- [API Gateway Docs](https://docs.aws.amazon.com/apigateway/)
- [AWS WAF Docs](https://docs.aws.amazon.com/waf/)
- [A2A Protocol](https://a2a-protocol.org)

