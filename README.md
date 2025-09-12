# Bedrock Agent Maintenance System

An AI-powered maintenance expert system built with AWS Bedrock that provides intelligent analysis and recommendations for industrial equipment monitoring.

## Project Structure

```
├── lambda_functions/           # AWS Lambda functions
│   ├── query_handler/         # Main query processing function
│   ├── session_manager/       # Session lifecycle management
│   ├── data_sync/            # Knowledge Base synchronization
│   └── health_check/         # System health monitoring
├── streamlit_app/            # Web interface
│   ├── app.py               # Main Streamlit application
│   └── requirements.txt     # Streamlit dependencies
├── config/                  # Configuration files
│   ├── aws_config.json     # AWS resource configuration
│   └── iam_policies.json   # IAM policy definitions
├── deploy.py               # Deployment script
├── requirements.txt        # Main project dependencies
└── README.md              # This file
```

## Lambda Functions

### query_handler
- **Purpose**: Processes incoming queries and manages Bedrock Agent interactions
- **Function URL**: Enabled with CORS for Streamlit integration
- **Runtime**: Python 3.11
- **Timeout**: 300 seconds

### session_manager
- **Purpose**: Handles conversation session lifecycle and history
- **Function URL**: Enabled for session management endpoints
- **Runtime**: Python 3.11
- **Timeout**: 60 seconds

### data_sync
- **Purpose**: Manages Knowledge Base synchronization with S3 data
- **Trigger**: EventBridge scheduled events
- **Runtime**: Python 3.11
- **Timeout**: 900 seconds

### health_check
- **Purpose**: System health monitoring and status reporting
- **Function URL**: Public endpoint for health checks
- **Runtime**: Python 3.11
- **Timeout**: 30 seconds

## Streamlit Application

The web interface provides:
- Interactive chat interface for natural language queries
- Equipment filtering and time range selection
- Conversation history and session management
- Real-time response display with source citations

## Configuration

### AWS Resources
- **Region**: us-west-2 (configurable)
- **Bedrock Agent**: maintenance-expert-agent
- **Knowledge Base**: maintenance-fault-data-kb
- **S3 Bucket**: relu-quicksight

### IAM Roles
- **Lambda Execution Role**: bedrock-agent-lambda-execution-role
- **Bedrock Agent Role**: bedrock-agent-service-role
- **Knowledge Base Role**: bedrock-knowledge-base-role

## Getting Started

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS Credentials**
   ```bash
   aws configure
   ```

3. **Update Configuration**
   - Edit `config/aws_config.json` with your specific settings
   - Update region, bucket names, and other parameters as needed

4. **Deploy Infrastructure**
   ```bash
   python deploy.py
   ```

5. **Run Streamlit App Locally**
   ```bash
   cd streamlit_app
   streamlit run app.py
   ```

## Development Notes

This project follows a task-driven development approach. The current implementation provides:

- ✅ Basic project structure and templates
- ⏳ AWS resource creation (next task)
- ⏳ Bedrock Agent and Knowledge Base setup
- ⏳ Lambda function implementation
- ⏳ Streamlit integration
- ⏳ Testing and deployment

Each Lambda function includes placeholder implementations that will be completed in subsequent development tasks.

## Security

- IAM roles follow least-privilege principles
- Function URLs use appropriate authentication (IAM or public as needed)
- CORS configured for secure Streamlit integration
- All data encrypted in transit and at rest

## Monitoring

- CloudWatch logging enabled for all Lambda functions
- Health check endpoint for system monitoring
- Error tracking and alerting (to be implemented)

## Next Steps

1. Configure S3 access for existing fault data
2. Create Bedrock Knowledge Base
3. Create Bedrock Agent
4. Implement Lambda function logic
5. Complete Streamlit integration
6. Add comprehensive testing
7. Deploy to production environment