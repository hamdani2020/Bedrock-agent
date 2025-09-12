# Streamlit App Deployment Guide

## Deployment Information
- **Function URL**: https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/
- **Generated**: 2025-09-12 07:42:00
- **App Status**: ✅ Ready for deployment

## Local Testing
To test the Streamlit app locally:

```bash
# Install requirements
pip install -r streamlit_app/requirements.txt

# Run the app
streamlit run streamlit_app/app.py
```

The app will be available at `http://localhost:8501`

## Deployment Options

### Option 1: Streamlit Cloud (Recommended for Development)
1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Deploy Streamlit app"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to https://share.streamlit.io/
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file path: `streamlit_app/app.py`
   - Click "Deploy!"

3. **Configuration**
   - The app is pre-configured with the Function URL
   - No additional environment variables needed
   - CORS is already configured for Streamlit domains

### Option 2: Heroku (Production Ready)
1. **Create a Procfile**
   ```bash
   echo "web: streamlit run streamlit_app/app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile
   ```

2. **Create runtime.txt**
   ```bash
   echo "python-3.11.0" > runtime.txt
   ```

3. **Deploy to Heroku**
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

### Option 3: AWS ECS/Fargate (Enterprise Production)
1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY streamlit_app/requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY streamlit_app/ .
   
   EXPOSE 8501
   
   HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
   
   ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **Build and push to ECR**
   ```bash
   docker build -t maintenance-agent .
   # Push to ECR (requires AWS CLI configuration)
   ```

3. **Deploy using ECS service**
   - Create ECS cluster
   - Create task definition
   - Create service with load balancer

## Configuration

### Pre-configured Settings
- **Function URL**: https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/
- **CORS**: Configured for localhost and Streamlit domains
- **Authentication**: None required (public Function URL)

### Environment Variables (Optional)
If you need to override the Function URL:
```bash
export LAMBDA_FUNCTION_URL="your-function-url-here"
```

## Testing Checklist

### Pre-deployment Testing
- [x] App starts without errors
- [x] All imports successful
- [x] Function URL configured
- [x] Valid Python syntax
- [x] Required components present

### Post-deployment Testing
- [ ] App loads in browser
- [ ] Can connect to Lambda function
- [ ] Chat interface works
- [ ] Responses received from Bedrock Agent
- [ ] Error handling works properly
- [ ] Session management functions correctly
- [ ] CORS works for cross-origin requests

## Monitoring and Maintenance

### Application Monitoring
- Monitor Streamlit app performance and uptime
- Check user engagement and session duration
- Monitor error rates and user feedback

### Backend Monitoring
- Monitor Lambda function logs in CloudWatch
- Check Function URL metrics and response times
- Monitor Bedrock Agent usage and costs
- Track Knowledge Base sync status

### Performance Optimization
- Monitor response times (target: <30 seconds)
- Check concurrent user handling
- Optimize Lambda function memory/timeout if needed
- Monitor Knowledge Base query performance

## Troubleshooting

### Common Issues

1. **App won't start**
   - Check Python version compatibility
   - Verify all dependencies installed
   - Check for syntax errors in app.py

2. **Can't connect to Lambda function**
   - Verify Function URL is accessible
   - Check CORS configuration
   - Test Function URL directly with curl

3. **Slow responses**
   - Check Lambda function timeout settings
   - Monitor Bedrock Agent performance
   - Verify Knowledge Base is synced

4. **CORS errors in browser**
   - Verify Function URL CORS configuration
   - Check allowed origins include your domain
   - Test with different browsers

### Debug Commands

```bash
# Test Function URL directly
curl -X POST https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"query":"test","sessionId":"debug-test"}'

# Run Streamlit with debug info
streamlit run streamlit_app/app.py --logger.level=debug

# Check app structure
python test_streamlit_deployment.py
```

## Security Considerations

### Production Deployment
- Consider implementing authentication for production use
- Monitor usage patterns and implement rate limiting if needed
- Regularly update dependencies for security patches
- Use HTTPS for all deployments

### Data Privacy
- Session data is stored locally in browser
- No persistent storage of conversation history
- Function URL logs may contain query data

## Support and Updates

### Getting Help
1. Check CloudWatch logs for Lambda function errors
2. Review Streamlit app logs for frontend issues
3. Test Function URL directly to isolate issues
4. Check AWS Bedrock service status

### Updating the Application
1. Update code in your repository
2. Redeploy using your chosen platform
3. Test functionality after deployment
4. Monitor for any issues post-update

## Success Metrics

### Key Performance Indicators
- Response time: <30 seconds for 95% of queries
- Uptime: >99% availability
- User engagement: Session duration and query frequency
- Error rate: <5% of total requests

### Monitoring Dashboard
Consider setting up monitoring for:
- Application uptime and response times
- Lambda function invocations and errors
- Bedrock Agent usage and costs
- User session analytics

---

## Quick Start Commands

```bash
# Local development
pip install -r streamlit_app/requirements.txt
streamlit run streamlit_app/app.py

# Streamlit Cloud deployment
# 1. Push to GitHub
# 2. Connect at https://share.streamlit.io/
# 3. Deploy from streamlit_app/app.py

# Heroku deployment
echo "web: streamlit run streamlit_app/app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile
heroku create your-app-name
git push heroku main
```

**Status**: ✅ Ready for deployment
**Last Updated**: 2025-09-12 07:42:00