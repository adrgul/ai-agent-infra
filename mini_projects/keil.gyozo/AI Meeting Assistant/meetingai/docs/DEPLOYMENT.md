# Deployment Guide

## Local Development

### Prerequisites

- Python 3.11+
- pip
- virtualenv

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd meetingai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run tests**
   ```bash
   pytest
   ```

6. **Run local development**
   ```bash
   python scripts/run_local.py data/sample_meetings/example_transcript.txt
   ```

## Docker Deployment

### Build Docker Image

```bash
docker build -t meetingai .
```

### Run with Docker

```bash
# Basic run
docker run -v $(pwd)/data:/app/data meetingai process /app/data/sample_meetings/example_transcript.txt

# With environment variables
docker run --env-file .env -v $(pwd)/data:/app/data meetingai process /app/data/sample_meetings/example_transcript.txt
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  meetingai:
    build: .
    volumes:
      - ./data:/app/data
      - ./config.yaml:/app/config.yaml
    env_file:
      - .env
    command: process /app/data/sample_meetings/example_transcript.txt
```

Run with:

```bash
docker-compose up
```

## Cloud Deployment

### AWS Lambda

1. **Create Lambda function**
   ```bash
   # Package the application
   pip install -r requirements.txt -t .
   zip -r deployment.zip .
   ```

2. **Deploy to Lambda**
   ```bash
   aws lambda create-function \
     --function-name meetingai \
     --runtime python3.11 \
     --handler main.lambda_handler \
     --role arn:aws:iam::account:role/lambda-role \
     --zip-file fileb://deployment.zip
   ```

### Google Cloud Functions

1. **Deploy function**
   ```bash
   gcloud functions deploy meetingai \
     --runtime python311 \
     --trigger-http \
     --entry-point process_meeting \
     --set-env-vars CONFIG_PATH=config.yaml
   ```

### Azure Functions

1. **Create function app**
   ```bash
   az functionapp create \
     --resource-group myResourceGroup \
     --consumption-plan-location eastus \
     --runtime python \
     --runtime-version 3.11 \
     --functions-version 4 \
     --name meetingai \
     --storage-account myStorageAccount
   ```

2. **Deploy**
   ```bash
   func azure functionapp publish meetingai
   ```

## Server Deployment

### Using Gunicorn

1. **Install Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 main:app
   ```

### Using uWSGI

1. **Install uWSGI**
   ```bash
   pip install uwsgi
   ```

2. **Create uwsgi.ini**
   ```ini
   [uwsgi]
   module = main:app
   master = true
   processes = 4
   socket = 0.0.0.0:8000
   chmod-socket = 664
   vacuum = true
   die-on-term = true
   ```

3. **Run**
   ```bash
   uwsgi uwsgi.ini
   ```

## Integration Setup

### Jira Integration

1. **Get Jira API token**
   - Go to Jira Settings > Account > Security > API tokens
   - Create new token

2. **Configure permissions**
   - Ensure user has permission to create issues in target project

3. **Test connection**
   ```python
   from meetingai.integrations.jira_client import JiraClient
   client = JiraClient(config)
   # Test creating an issue
   ```

### Google Calendar Integration

1. **Create Google Cloud Project**
   - Enable Calendar API
   - Create OAuth 2.0 credentials

2. **Setup credentials**
   ```bash
   # Download credentials.json
   mv ~/Downloads/credentials.json .
   ```

3. **First run will prompt for authorization**

### Email Integration

#### SMTP
1. **Configure SMTP settings**
   ```yaml
   integrations:
     email:
       provider: "smtp"
       smtp_server: "smtp.gmail.com"
       smtp_port: 587
   ```

2. **Enable less secure apps** (for Gmail) or use App Passwords

#### SendGrid
1. **Get SendGrid API key**
   - Sign up at sendgrid.com
   - Create API key

2. **Configure**
   ```yaml
   integrations:
     email:
       provider: "sendgrid"
       # API key via environment variable
   ```

### Slack Integration

1. **Create Slack app**
   - Go to api.slack.com
   - Create new app

2. **Add webhook**
   - Add "Incoming Webhooks" feature
   - Create webhook URL

3. **Configure**
   ```yaml
   integrations:
     slack:
       webhook_url: "${SLACK_WEBHOOK_URL}"
   ```

## Monitoring and Logging

### Application Logs

Logs are configured via `config.yaml`:

```yaml
logging:
  level: "INFO"
  file: "./logs/meetingai.log"
  max_bytes: 10485760
  backup_count: 5
```

### Health Checks

Add health check endpoint:

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Metrics

Consider adding metrics with:

- Prometheus client
- Custom CloudWatch metrics
- Application Insights

## Security Considerations

### API Keys
- Store in environment variables
- Use secret management services (AWS Secrets Manager, Azure Key Vault)
- Rotate keys regularly

### Network Security
- Use HTTPS in production
- Configure firewalls
- Use VPC/security groups

### Data Protection
- Encrypt sensitive data
- Implement access controls
- Regular security audits

## Performance Optimization

### Caching
- Cache LLM responses for repeated requests
- Cache parsed documents

### Async Processing
- Use async/await for I/O operations
- Process multiple files concurrently

### Resource Limits
- Set memory limits for Lambda functions
- Configure timeouts appropriately

## Troubleshooting

### Common Issues

1. **LLM API errors**
   - Check API keys
   - Verify rate limits
   - Check network connectivity

2. **File parsing errors**
   - Verify file format support
   - Check file encoding (UTF-8)
   - Validate file size limits

3. **Integration failures**
   - Verify credentials
   - Check API permissions
   - Review integration-specific logs

### Debug Mode

Enable debug logging:

```yaml
logging:
  level: "DEBUG"
```

Run with verbose output:

```bash
python -m meetingai process --verbose meeting.txt
```