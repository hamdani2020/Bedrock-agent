"""
Prepare S3 analytics data for Bedrock Knowledge Base ingestion
This script processes your fault prediction data into knowledge base friendly format
"""

import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Configuration
SOURCE_BUCKET = "relu-quicksight"
SOURCE_PREFIX = "bedrock-recommendations/analytics/"
KB_BUCKET = "relu-quicksight"  # Can use same bucket
KB_PREFIX = "knowledge-base-data/"

def create_knowledge_base_documents():
    """
    Convert analytics data into knowledge base documents
    Each document contains contextual information about equipment faults
    """
    
    s3_client = boto3.client('s3')
    
    # List all analytics files
    response = s3_client.list_objects_v2(
        Bucket=SOURCE_BUCKET,
        Prefix=SOURCE_PREFIX
    )
    
    documents = []
    
    for obj in response.get('Contents', []):
        key = obj['Key']
        
        # Read analytics file
        file_response = s3_client.get_object(Bucket=SOURCE_BUCKET, Key=key)
        analytics_data = json.loads(file_response['Body'].read())
        
        # Create knowledge base document
        document = create_kb_document(analytics_data)
        documents.append(document)
    
    # Save consolidated knowledge base file
    save_kb_documents(documents)
    
    return len(documents)

def create_kb_document(analytics_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a knowledge base document from analytics data"""
    
    # Extract key information
    timestamp = analytics_data.get('timestamp', '')
    date = analytics_data.get('date', '')
    fault = analytics_data.get('predicted_fault', 'Unknown')
    risk_level = analytics_data.get('risk_level', 'UNKNOWN')
    
    # Sensor readings
    speed = analytics_data.get('speed_rpm', 0)
    load = analytics_data.get('load_units', 0)
    current = analytics_data.get('current_amps', 0)
    temperature = analytics_data.get('temperature_celsius', 0)
    vibration = analytics_data.get('vibration_mms', 0)
    
    # Create descriptive text for semantic search
    content = f"""
    EQUIPMENT FAULT ANALYSIS REPORT
    
    Date: {date}
    Time: {timestamp}
    
    FAULT PREDICTION: {fault}
    Risk Level: {risk_level}
    Equipment Type: Industrial Conveyor System
    
    SENSOR READINGS:
    - Speed: {speed} RPM
    - Load: {load} units  
    - Current: {current} Amps
    - Temperature: {temperature}°C
    - Vibration: {vibration} mm/s
    
    SENSOR STATUS:
    - Speed Status: {analytics_data.get('speed_status', 'Unknown')}
    - Load Status: {analytics_data.get('load_status', 'Unknown')}
    - Current Status: {analytics_data.get('current_status', 'Unknown')}
    - Temperature Status: {analytics_data.get('temperature_status', 'Unknown')}
    - Vibration Status: {analytics_data.get('vibration_status', 'Unknown')}
    
    FAULT ANALYSIS:
    Fault Category: {analytics_data.get('fault_category', 'Unknown')}
    Critical Fault: {'Yes' if analytics_data.get('is_critical_fault') else 'No'}
    Immediate Action Required: {'Yes' if analytics_data.get('requires_immediate_action') else 'No'}
    
    MAINTENANCE RECOMMENDATION:
    {analytics_data.get('recommendation_summary', 'No recommendation available')}
    
    CONTEXT FOR ANALYSIS:
    This fault occurred on {date} with {risk_level} risk level. The primary indicators were:
    {get_primary_indicators(analytics_data)}
    
    HISTORICAL PATTERN:
    This type of fault ({fault}) typically occurs when:
    {get_fault_pattern_description(fault, analytics_data)}
    """
    
    # Create document with metadata
    document = {
        'content': content.strip(),
        'metadata': {
            'timestamp': timestamp,
            'date': date,
            'fault_type': fault,
            'risk_level': risk_level,
            'equipment_type': 'industrial_conveyor',
            'vibration_level': vibration,
            'temperature': temperature,
            'is_critical': analytics_data.get('is_critical_fault', 0),
            'document_type': 'fault_analysis'
        }
    }
    
    return document

def get_primary_indicators(analytics_data: Dict[str, Any]) -> str:
    """Generate description of primary fault indicators"""
    
    indicators = []
    
    # Check each sensor status
    if analytics_data.get('vibration_status') == 'CRITICAL':
        indicators.append(f"Critical vibration level ({analytics_data.get('vibration_mms')} mm/s)")
    
    if analytics_data.get('temperature_status') == 'CRITICAL':
        indicators.append(f"High temperature ({analytics_data.get('temperature_celsius')}°C)")
        
    if analytics_data.get('current_status') == 'CRITICAL':
        indicators.append(f"Excessive current draw ({analytics_data.get('current_amps')} Amps)")
    
    if analytics_data.get('speed_status') == 'CRITICAL':
        indicators.append(f"Abnormal speed ({analytics_data.get('speed_rpm')} RPM)")
        
    if analytics_data.get('load_status') == 'CRITICAL':
        indicators.append(f"High load condition ({analytics_data.get('load_units')} units)")
    
    return ', '.join(indicators) if indicators else 'All sensors within normal ranges'

def get_fault_pattern_description(fault_type: str, analytics_data: Dict[str, Any]) -> str:
    """Generate pattern description for each fault type"""
    
    patterns = {
        'Ball Bearing Fault': f"vibration levels exceed 2.0 mm/s (current: {analytics_data.get('vibration_mms')} mm/s), often accompanied by temperature increases due to friction",
        
        'Drive Motor Fault': f"current draw exceeds 5.0 Amps (current: {analytics_data.get('current_amps')} Amps), indicating electrical issues or mechanical binding",
        
        'Central Shaft Fault': f"multiple sensor anomalies occur simultaneously, indicating structural or alignment issues affecting the entire system",
        
        'Pulley Fault': f"moderate vibration increases (1.0-2.0 mm/s) combined with speed variations, suggesting pulley wear or misalignment",
        
        'Idler Roller Fault': f"localized vibration increases and belt tracking issues, typically showing vibration levels of 1.5-2.5 mm/s",
        
        'Belt Slippage': f"speed variations occur with normal vibration levels, often during high load conditions (>{analytics_data.get('load_units', 500)} units)",
        
        'Normal Operation': "all sensor readings remain within optimal ranges with stable performance indicators"
    }
    
    return patterns.get(fault_type, "sensor readings deviate from normal operating parameters")

def save_kb_documents(documents: List[Dict[str, Any]]):
    """Save documents for knowledge base ingestion"""
    
    s3_client = boto3.client('s3')
    
    # Create consolidated file for knowledge base
    kb_data = {
        'documents': documents,
        'metadata': {
            'created_at': datetime.utcnow().isoformat(),
            'document_count': len(documents),
            'data_source': 'industrial_equipment_fault_predictions',
            'version': '1.0'
        }
    }
    
    # Save to S3
    key = f"{KB_PREFIX}fault_analysis_knowledge_base.json"
    
    s3_client.put_object(
        Bucket=KB_BUCKET,
        Key=key,
        Body=json.dumps(kb_data, indent=2),
        ContentType='application/json',
        Metadata={
            'document_type': 'knowledge_base',
            'document_count': str(len(documents)),
            'created_at': datetime.utcnow().isoformat()
        }
    )
    
    print(f"Saved {len(documents)} documents to s3://{KB_BUCKET}/{key}")

if __name__ == "__main__":
    # Run the knowledge base preparation
    doc_count = create_knowledge_base_documents()
    print(f"Successfully processed {doc_count} fault analysis documents for knowledge base")