#!/usr/bin/env python3
"""
Debug the ingestion issue and create better text content
"""

import boto3
import json
from botocore.exceptions import ClientError

def load_config():
    """Load AWS configuration"""
    try:
        with open('config/aws_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Config file not found")
        return None

def download_and_examine_json():
    """Download and examine the original JSON data"""
    config = load_config()
    if not config:
        return None
    
    try:
        s3 = boto3.client('s3', region_name=config['region'])
        
        bucket_name = config['s3']['data_bucket']['name']
        json_key = "bedrock-recommendations/analytics/2025/09/11/analytics_20250911_122655_572660.json"
        
        print(f"📥 Downloading original JSON: {json_key}")
        
        response = s3.get_object(Bucket=bucket_name, Key=json_key)
        json_content = response['Body'].read().decode('utf-8')
        
        print(f"📄 Raw JSON content:")
        print(json_content)
        print("\n" + "="*50)
        
        # Parse JSON
        data = json.loads(json_content)
        print(f"📊 Parsed JSON structure:")
        for key, value in data.items():
            print(f"   {key}: {type(value)} = {value}")
        
        return data
        
    except ClientError as e:
        print(f"❌ Error downloading JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def create_comprehensive_text(json_data):
    """Create comprehensive text from the full JSON data"""
    if not json_data:
        return None
    
    print("\n🔄 Creating comprehensive text content...")
    
    text_lines = []
    
    # Header
    text_lines.append("EQUIPMENT MAINTENANCE ANALYTICS REPORT")
    text_lines.append("=" * 50)
    text_lines.append("")
    
    # Basic Information
    text_lines.append("REPORT INFORMATION")
    text_lines.append("-" * 20)
    text_lines.append(f"Timestamp: {json_data.get('timestamp', 'Unknown')}")
    text_lines.append(f"Date: {json_data.get('date', 'Unknown')}")
    text_lines.append(f"Hour: {json_data.get('hour', 'Unknown')}")
    text_lines.append(f"Day of Week: {json_data.get('day_of_week', 'Unknown')}")
    text_lines.append(f"Month: {json_data.get('month', 'Unknown')}")
    text_lines.append(f"Year: {json_data.get('year', 'Unknown')}")
    text_lines.append("")
    
    # Equipment Information
    text_lines.append("EQUIPMENT INFORMATION")
    text_lines.append("-" * 25)
    text_lines.append(f"Equipment ID: {json_data.get('equipment_id', 'Unknown')}")
    text_lines.append(f"Equipment Type: {json_data.get('equipment_type', 'Unknown')}")
    text_lines.append(f"Inference ID: {json_data.get('inference_id', 'Unknown')}")
    text_lines.append("")
    
    # Sensor Readings
    if 'sensor_readings' in json_data:
        text_lines.append("CURRENT SENSOR READINGS")
        text_lines.append("-" * 25)
        sensors = json_data['sensor_readings']
        for sensor_name, value in sensors.items():
            formatted_name = sensor_name.replace('_', ' ').title()
            text_lines.append(f"{formatted_name}: {value}")
        text_lines.append("")
    
    # Fault Prediction
    if 'fault_prediction' in json_data:
        text_lines.append("FAULT PREDICTION ANALYSIS")
        text_lines.append("-" * 30)
        prediction = json_data['fault_prediction']
        
        text_lines.append(f"Fault Probability: {prediction.get('probability', 'Unknown')}")
        text_lines.append(f"Risk Level: {prediction.get('risk_level', 'Unknown')}")
        text_lines.append(f"Predicted Failure Date: {prediction.get('predicted_failure_date', 'Unknown')}")
        
        if 'confidence_score' in prediction:
            text_lines.append(f"Confidence Score: {prediction['confidence_score']}")
        
        text_lines.append("")
    
    # Maintenance Recommendations
    if 'maintenance_recommendations' in json_data:
        text_lines.append("MAINTENANCE RECOMMENDATIONS")
        text_lines.append("-" * 35)
        recommendations = json_data['maintenance_recommendations']
        
        text_lines.append(f"Priority Level: {recommendations.get('priority', 'Unknown')}")
        text_lines.append(f"Recommended Action: {recommendations.get('action', 'No action specified')}")
        text_lines.append(f"Estimated Cost: ${recommendations.get('estimated_cost', 'Unknown')}")
        text_lines.append(f"Urgency: {recommendations.get('urgency', 'Unknown')}")
        
        if 'timeline' in recommendations:
            text_lines.append(f"Timeline: {recommendations['timeline']}")
        
        text_lines.append("")
    
    # Analysis
    if 'analysis' in json_data:
        text_lines.append("DETAILED ANALYSIS")
        text_lines.append("-" * 20)
        text_lines.append(json_data['analysis'])
        text_lines.append("")
    
    # Historical Context
    if 'historical_context' in json_data:
        text_lines.append("HISTORICAL CONTEXT")
        text_lines.append("-" * 20)
        text_lines.append(json_data['historical_context'])
        text_lines.append("")
    
    # Performance Metrics
    if 'performance_metrics' in json_data:
        text_lines.append("PERFORMANCE METRICS")
        text_lines.append("-" * 22)
        metrics = json_data['performance_metrics']
        for metric_name, value in metrics.items():
            formatted_name = metric_name.replace('_', ' ').title()
            text_lines.append(f"{formatted_name}: {value}")
        text_lines.append("")
    
    # Add all other fields that might exist
    excluded_fields = {
        'timestamp', 'date', 'hour', 'day_of_week', 'month', 'year',
        'equipment_id', 'equipment_type', 'inference_id',
        'sensor_readings', 'fault_prediction', 'maintenance_recommendations',
        'analysis', 'historical_context', 'performance_metrics'
    }
    
    other_fields = {k: v for k, v in json_data.items() if k not in excluded_fields}
    if other_fields:
        text_lines.append("ADDITIONAL DATA")
        text_lines.append("-" * 15)
        for key, value in other_fields.items():
            formatted_key = key.replace('_', ' ').title()
            text_lines.append(f"{formatted_key}: {value}")
        text_lines.append("")
    
    # Footer
    text_lines.append("END OF REPORT")
    text_lines.append("=" * 50)
    
    return "\n".join(text_lines)

def upload_improved_text(text_content):
    """Upload the improved text content"""
    config = load_config()
    if not config:
        return False
    
    try:
        s3 = boto3.client('s3', region_name=config['region'])
        
        bucket_name = config['s3']['data_bucket']['name']
        prefix = config['s3']['data_bucket']['data_structure']['base_prefix']
        
        # Create improved text file
        text_key = f"{prefix}improved_analytics_report.txt"
        
        print(f"📤 Uploading improved text to: {text_key}")
        
        s3.put_object(
            Bucket=bucket_name,
            Key=text_key,
            Body=text_content.encode('utf-8'),
            ContentType='text/plain'
        )
        
        print(f"✅ Successfully uploaded improved text file")
        return True
        
    except ClientError as e:
        print(f"❌ Error uploading text: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Debugging ingestion and creating improved text content...\n")
    
    # Download and examine original JSON
    json_data = download_and_examine_json()
    
    if json_data:
        # Create comprehensive text
        text_content = create_comprehensive_text(json_data)
        
        if text_content:
            print(f"\n📄 Generated text content ({len(text_content)} characters):")
            print(text_content[:500] + "..." if len(text_content) > 500 else text_content)
            
            # Upload improved text
            upload_improved_text(text_content)
    
    print("\n" + "="*50)
    print("✅ Debug and improvement complete!")

if __name__ == "__main__":
    main()