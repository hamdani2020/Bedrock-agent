import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime')
s3_client = boto3.client('s3')

# Configuration
BEDROCK_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"  # Claude 3 Haiku - Available in eu-west-1
S3_BUCKET = "relu-quicksight"  # QuickSight data bucket
S3_PREFIX = "bedrock-recommendations/"

def lambda_handler(event, context):
    """
    Lambda function that:
    1. Receives inference output from SageMaker
    2. Sends it to Bedrock for recommendations
    3. Saves the recommendation to S3
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract inference data from the event
        inference_data = extract_inference_data(event)
        
        # Generate recommendation using Bedrock
        recommendation = get_bedrock_recommendation(inference_data)
        
        # Save to S3
        s3_key = save_to_s3(inference_data, recommendation)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed inference and generated recommendation',
                's3_location': f"s3://{S3_BUCKET}/{s3_key}",
                'recommendation_summary': recommendation.get('summary', 'No summary available')
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing inference: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to process inference data'
            })
        }

def extract_inference_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and validate industrial equipment sensor data and predictions"""
    
    # Handle different event sources
    if 'Records' in event:
        # S3 event trigger
        record = event['Records'][0]
        if record['eventSource'] == 'aws:s3':
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            # Read inference data from S3
            response = s3_client.get_object(Bucket=bucket, Key=key)
            inference_data = json.loads(response['Body'].read())
            
    elif 'inference_result' in event:
        # Direct SageMaker inference result
        inference_data = event['inference_result']
        
    elif 'body' in event:
        # API Gateway event
        inference_data = json.loads(event['body'])
        
    else:
        # Direct Lambda invocation with sensor data + prediction
        inference_data = event
    
    # Extract sensor data (input features)
    sensor_data = {
        'speed': inference_data.get('speed'),
        'load': inference_data.get('load'), 
        'current': inference_data.get('current'),
        'temperature': inference_data.get('temperature'),
        'vibration': inference_data.get('vibration')
    }
    
    # Validate sensor data
    required_sensor_fields = ['speed', 'load', 'current', 'temperature', 'vibration']
    for field in required_sensor_fields:
        if sensor_data[field] is None:
            raise ValueError(f"Missing required sensor field: {field}")
    
    # Extract prediction results (from ML model output)
    prediction = inference_data.get('prediction')
    
    if prediction is None:
        raise ValueError("Missing prediction result from ML model")
    
    # No confidence score provided by ML model - will use prediction certainty logic
    
    # Validate prediction is one of expected fault types
    valid_predictions = [
        'Ball Bearing Fault',
        'Central Shaft Fault', 
        'Pulley Fault',
        'Drive Motor Fault',
        'Idler Roller Fault',
        'Belt Slippage',
        'Normal Operation'  # Assuming this is also possible
    ]
    
    if prediction not in valid_predictions:
        logger.warning(f"Unexpected prediction value: {prediction}")
    
    # Generate timestamp since input doesn't include it
    current_timestamp = datetime.utcnow().isoformat()
    
    # Structure the inference data
    structured_data = {
        'inference_id': f"fault_pred_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
        'timestamp': current_timestamp,  # Generated timestamp for processing time
        'original_timestamp': inference_data.get('timestamp'),  # In case it's provided
        'sensor_data': sensor_data,
        'prediction': prediction,
        'confidence': None,  # No confidence score from ML model
        'equipment_type': 'industrial_conveyor',  # Based on your fault types
        'processing_stage': 'inference_complete'
    }
    
    return structured_data

def get_bedrock_recommendation(inference_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send inference data to Bedrock and get recommendation"""
    
    # Prepare the prompt for Bedrock
    prompt = create_bedrock_prompt(inference_data)
    
    # Prepare the request body for Claude
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
        "top_p": 0.9
    }
    
    try:
        # Call Bedrock
        logger.info("Sending request to Bedrock...")
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        recommendation_text = response_body['content'][0]['text']
        
        # Structure the recommendation
        recommendation = {
            'raw_response': recommendation_text,
            'summary': extract_summary(recommendation_text),
            'action_items': extract_action_items(recommendation_text),
            'risk_level': extract_risk_level(recommendation_text),
            'timestamp': datetime.utcnow().isoformat(),
            'model_used': BEDROCK_MODEL_ID
        }
        
        logger.info("Successfully received recommendation from Bedrock")
        return recommendation
        
    except Exception as e:
        logger.error(f"Error calling Bedrock: {str(e)}")
        raise

def create_bedrock_prompt(inference_data: Dict[str, Any]) -> str:
    """Create a structured prompt for industrial equipment fault prediction"""
    
    sensor_data = inference_data.get('sensor_data', {})
    prediction = inference_data.get('prediction')
    confidence = inference_data.get('confidence')
    equipment_type = inference_data.get('equipment_type', 'industrial_conveyor')
    
    # Create context about the fault type
    fault_context = get_fault_context(prediction)
    
    prompt = f"""
    You are an expert industrial maintenance engineer specializing in conveyor belt systems and rotating machinery. 
    Analyze the following sensor data and ML fault prediction to provide specific maintenance recommendations.

    EQUIPMENT TYPE: {equipment_type}
    
    CURRENT SENSOR READINGS:
    - Speed: {sensor_data.get('speed', 'N/A')} RPM
    - Load: {sensor_data.get('load', 'N/A')} units
    - Current: {sensor_data.get('current', 'N/A')} Amps
    - Temperature: {sensor_data.get('temperature', 'N/A')}°C
    - Vibration: {sensor_data.get('vibration', 'N/A')} mm/s

    ML FAULT PREDICTION: {prediction}
    CONFIDENCE LEVEL: Not provided by ML model
    
    FAULT CONTEXT: {fault_context}

    Based on this analysis, provide:

    1. SUMMARY: Current equipment status and predicted fault severity
    
    2. RISK ASSESSMENT: Classify risk level as LOW/MEDIUM/HIGH based on:
       - Fault type severity
       - Confidence level
       - Sensor readings deviation from normal ranges
    
    3. RECOMMENDATIONS: Specific maintenance actions for this fault type:
       - Immediate actions (if any)
       - Scheduled maintenance tasks
       - Parts to inspect/replace
       - Monitoring frequency adjustments
    
    4. PRIORITY ACTIONS: If confidence > 80% and fault is critical, list urgent steps
    
    5. ESTIMATED TIMELINE: When maintenance should be performed (immediate/within 24h/within week/scheduled)

    Format your response clearly with these exact section headers for parsing.
    """
    
    return prompt

def get_fault_context(prediction: str) -> str:
    """Provide context about specific fault types"""
    
    fault_contexts = {
        'Ball Bearing Fault': 'Ball bearing failures typically cause increased vibration and temperature. Can lead to catastrophic failure if not addressed promptly. Common causes: inadequate lubrication, contamination, misalignment.',
        
        'Central Shaft Fault': 'Central shaft issues affect entire system operation. May indicate wear, misalignment, or structural damage. Critical component requiring immediate attention to prevent system shutdown.',
        
        'Pulley Fault': 'Pulley problems can cause belt slippage, uneven wear, and reduced efficiency. May indicate bearing wear, misalignment, or pulley surface damage.',
        
        'Drive Motor Fault': 'Motor faults can cause system shutdown and are often expensive to repair. May indicate electrical issues, bearing problems, or overheating. Requires electrical safety precautions.',
        
        'Idler Roller Fault': 'Idler roller issues cause belt tracking problems and increased wear. Usually indicates bearing failure or roller surface damage. Can cause belt damage if not addressed.',
        
        'Belt Slippage': 'Belt slippage reduces efficiency and causes premature wear. May indicate incorrect tension, pulley wear, or contamination. Often easiest fault to correct.',
        
        'Normal Operation': 'System operating within normal parameters. Continue regular monitoring and preventive maintenance schedule.'
    }
    
    return fault_contexts.get(prediction, 'Unknown fault type - requires expert analysis.')

def extract_summary(text: str) -> str:
    """Extract summary from Bedrock response"""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'SUMMARY' in line.upper():
            # Get the next non-empty line
            for j in range(i+1, len(lines)):
                if lines[j].strip():
                    return lines[j].strip()
    return "No summary available"

def extract_action_items(text: str) -> list:
    """Extract action items from Bedrock response"""
    action_items = []
    lines = text.split('\n')
    in_recommendations = False
    
    for line in lines:
        if 'RECOMMENDATION' in line.upper():
            in_recommendations = True
            continue
        if 'PRIORITY' in line.upper():
            break
        if in_recommendations and line.strip():
            if line.strip().startswith(('-', '*', '•')):
                action_items.append(line.strip()[1:].strip())
    
    return action_items

def extract_risk_level(text: str) -> str:
    """Extract risk level from Bedrock response"""
    text_upper = text.upper()
    if 'HIGH' in text_upper and 'RISK' in text_upper:
        return 'HIGH'
    elif 'MEDIUM' in text_upper and 'RISK' in text_upper:
        return 'MEDIUM'
    elif 'LOW' in text_upper and 'RISK' in text_upper:
        return 'LOW'
    return 'UNKNOWN'

def save_to_s3(inference_data: Dict[str, Any], recommendation: Dict[str, Any]) -> str:
    """Save data optimized for QuickSight visualization"""
    
    current_time = datetime.utcnow()
    timestamp_str = current_time.strftime('%Y%m%d_%H%M%S_%f')
    
    # 1. Save detailed JSON for debugging/audit trail
    detailed_data = create_detailed_record(inference_data, recommendation, current_time)
    detailed_key = save_detailed_json(detailed_data, current_time, timestamp_str)
    
    # 2. Save flattened data for QuickSight analytics
    flattened_data = create_flattened_record(inference_data, recommendation, current_time)
    analytics_key = save_analytics_record(flattened_data, current_time, timestamp_str)
    
    logger.info(f"Saved detailed data: s3://{S3_BUCKET}/{detailed_key}")
    logger.info(f"Saved analytics data: s3://{S3_BUCKET}/{analytics_key}")
    
    return detailed_key

def create_detailed_record(inference_data: Dict[str, Any], recommendation: Dict[str, Any], timestamp: datetime) -> Dict[str, Any]:
    """Create detailed record with full nested data"""
    return {
        'inference_data': inference_data,
        'bedrock_recommendation': recommendation,
        'processing_metadata': {
            'processed_at': timestamp.isoformat(),
            'lambda_function': 'inference_to_bedrock_lambda',
            'version': '1.0',
            'record_type': 'detailed'
        }
    }

def create_flattened_record(inference_data: Dict[str, Any], recommendation: Dict[str, Any], timestamp: datetime) -> Dict[str, Any]:
    """Create flattened record optimized for QuickSight analytics - Industrial Equipment Focus"""
    
    # Extract sensor data fields for industrial equipment
    sensor_data = inference_data.get('sensor_data', {})
    
    # Create analytics-friendly flat record
    return {
        # Timestamp fields for time-series analysis
        'timestamp': timestamp.isoformat(),
        'date': timestamp.strftime('%Y-%m-%d'),
        'hour': timestamp.hour,
        'day_of_week': timestamp.strftime('%A'),
        'month': timestamp.strftime('%Y-%m'),
        'year': timestamp.year,
        
        # Equipment identification
        'equipment_type': inference_data.get('equipment_type', 'industrial_conveyor'),
        'inference_id': inference_data.get('inference_id', f"fault_pred_{timestamp.strftime('%Y%m%d_%H%M%S')}"),
        
        # Sensor readings (direct mapping for industrial equipment)
        'speed_rpm': float(sensor_data.get('speed', 0)),
        'load_units': float(sensor_data.get('load', 0)),
        'current_amps': float(sensor_data.get('current', 0)),
        'temperature_celsius': float(sensor_data.get('temperature', 0)),
        'vibration_mms': float(sensor_data.get('vibration', 0)),
        
        # Fault prediction results
        'predicted_fault': inference_data.get('prediction', 'Unknown'),
        'fault_category': categorize_fault_type(inference_data.get('prediction', 'Unknown')),
        'confidence_score': None,  # No confidence from ML model
        'confidence_category': 'NOT_PROVIDED',
        
        # Operational status indicators
        'is_normal_operation': 1 if inference_data.get('prediction') == 'Normal Operation' else 0,
        'is_critical_fault': 1 if is_critical_fault(inference_data.get('prediction', '')) else 0,
        'requires_immediate_action': 1 if is_critical_fault(inference_data.get('prediction', '')) else 0,
        
        # Sensor health indicators (based on typical ranges)
        'speed_status': categorize_sensor_reading('speed', sensor_data.get('speed', 0)),
        'load_status': categorize_sensor_reading('load', sensor_data.get('load', 0)),
        'current_status': categorize_sensor_reading('current', sensor_data.get('current', 0)),
        'temperature_status': categorize_sensor_reading('temperature', sensor_data.get('temperature', 0)),
        'vibration_status': categorize_sensor_reading('vibration', sensor_data.get('vibration', 0)),
        
        # AI recommendation data (flattened)
        'recommendation_id': f"rec_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}",
        'risk_level': recommendation.get('risk_level', 'UNKNOWN'),
        'risk_score': map_risk_to_score(recommendation.get('risk_level', 'UNKNOWN')),
        'recommendation_summary': recommendation.get('summary', ''),
        'action_items_count': len(recommendation.get('action_items', [])),
        'model_used': recommendation.get('model_used', ''),
        
        # Processing metadata
        'processing_time_ms': calculate_processing_time_ms(inference_data, timestamp),
        'record_type': 'analytics'
    }

def categorize_fault_type(prediction: str) -> str:
    """Categorize fault types for easier filtering in QuickSight"""
    fault_categories = {
        'Ball Bearing Fault': 'BEARING',
        'Central Shaft Fault': 'MECHANICAL',
        'Pulley Fault': 'MECHANICAL', 
        'Drive Motor Fault': 'ELECTRICAL',
        'Idler Roller Fault': 'BEARING',
        'Belt Slippage': 'BELT',
        'Normal Operation': 'NORMAL'
    }
    return fault_categories.get(prediction, 'UNKNOWN')

def is_critical_fault(prediction: str) -> bool:
    """Determine if fault type is critical and requires immediate attention"""
    critical_faults = [
        'Central Shaft Fault',
        'Drive Motor Fault',
        'Ball Bearing Fault'  # High vibration can lead to catastrophic failure
    ]
    return prediction in critical_faults

def categorize_sensor_reading(sensor_type: str, value: float) -> str:
    """Categorize sensor readings as NORMAL/WARNING/CRITICAL based on typical ranges"""
    
    # Define typical operating ranges for industrial conveyor equipment
    ranges = {
        'speed': {'normal': (50, 200), 'warning': (30, 250), 'critical': (0, 300)},
        'load': {'normal': (100, 800), 'warning': (50, 1000), 'critical': (0, 1200)},
        'current': {'normal': (1.0, 5.0), 'warning': (0.5, 7.0), 'critical': (0, 10.0)},
        'temperature': {'normal': (20, 60), 'warning': (15, 80), 'critical': (0, 100)},
        'vibration': {'normal': (0.1, 1.0), 'warning': (0.05, 2.0), 'critical': (0, 5.0)}
    }
    
    if sensor_type not in ranges:
        return 'UNKNOWN'
    
    sensor_ranges = ranges[sensor_type]
    
    if sensor_ranges['normal'][0] <= value <= sensor_ranges['normal'][1]:
        return 'NORMAL'
    elif sensor_ranges['warning'][0] <= value <= sensor_ranges['warning'][1]:
        return 'WARNING'
    else:
        return 'CRITICAL'

def categorize_confidence(confidence: float) -> str:
    """Categorize confidence score for easier filtering in QuickSight"""
    if confidence >= 0.9:
        return 'HIGH'
    elif confidence >= 0.7:
        return 'MEDIUM'
    elif confidence >= 0.5:
        return 'LOW'
    else:
        return 'VERY_LOW'

def map_risk_to_score(risk_level: str) -> int:
    """Convert risk level to numeric score for QuickSight calculations"""
    risk_mapping = {
        'LOW': 1,
        'MEDIUM': 2,
        'HIGH': 3,
        'UNKNOWN': 0
    }
    return risk_mapping.get(risk_level.upper(), 0)

def calculate_processing_time_ms(inference_data: Dict[str, Any], end_time: datetime) -> float:
    """Calculate processing time in milliseconds"""
    try:
        start_time_str = inference_data.get('timestamp', end_time.isoformat())
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        return (end_time - start_time).total_seconds() * 1000
    except:
        return 0.0

def save_detailed_json(data: Dict[str, Any], timestamp: datetime, timestamp_str: str) -> str:
    """Save detailed JSON for audit trail"""
    date_path = timestamp.strftime('%Y/%m/%d/%H')
    filename = f"detailed_{timestamp_str}.json"
    s3_key = f"{S3_PREFIX}detailed/{date_path}/{filename}"
    
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=json.dumps(data, indent=2),
        ContentType='application/json',
        Metadata={
            'record_type': 'detailed',
            'risk_level': data['bedrock_recommendation'].get('risk_level', 'unknown'),
            'confidence': str(data['inference_data'].get('confidence', 0)),
            'processed_at': timestamp.isoformat()
        }
    )
    return s3_key

def save_analytics_record(data: Dict[str, Any], timestamp: datetime, timestamp_str: str) -> str:
    """Save flattened record for QuickSight analytics"""
    
    # Organize by date for efficient QuickSight queries
    date_path = timestamp.strftime('%Y/%m/%d')
    filename = f"analytics_{timestamp_str}.json"
    s3_key = f"{S3_PREFIX}analytics/{date_path}/{filename}"
    
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=json.dumps(data),  # No indentation for smaller file size
        ContentType='application/json',
        Metadata={
            'record_type': 'analytics',
            'risk_level': data.get('risk_level', 'unknown'),
            'confidence_category': data.get('confidence_category', 'unknown'),
            'date': data.get('date', ''),
            'processed_at': timestamp.isoformat()
        },
        # Add tags for better organization in S3
        Tagging=f"RecordType=analytics&RiskLevel={data.get('risk_level', 'unknown')}&Date={data.get('date', '')}"
    )
    return s3_key