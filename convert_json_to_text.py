#!/usr/bin/env python3
"""
Convert JSON analytics data to text format for better Knowledge Base ingestion
"""

import boto3
import json
from datetime import datetime
from botocore.exceptions import ClientError

def load_config():
    """Load AWS configuration"""
    try:
        with open('config/aws_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Config file not found")
        return None

def download_json_data():
    """Download existing JSON data from S3"""
    config = load_config()
    if not config:
        return None
    
    try:
        s3 = boto3.client('s3', region_name=config['region'])
        
        bucket_name = config['s3']['data_bucket']['name']
        prefix = config['s3']['data_bucket']['data_structure']['base_prefix']
        
        print(f"📥 Downloading JSON data from s3://{bucket_name}/{prefix}")
        
        # List objects with the prefix
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        objects = response.get('Contents', [])
        if not objects:
            print("❌ No JSON files found")
            return None
        
        # Download the first JSON file
        json_key = objects[0]['Key']
        print(f"   Downloading: {json_key}")
        
        response = s3.get_object(Bucket=bucket_name, Key=json_key)
        json_content = response['Body'].read().decode('utf-8')
        
        return json.loads(json_content), json_key
        
    except ClientError as e:
        print(f"❌ Error downloading JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def convert_to_text(json_data):
    """Convert JSON data to readable text format"""
    if not json_data:
        return None
    
    print("🔄 Converting JSON to text format...")
    
    text_content = []
    
    # Add header
    text_content.append("EQUIPMENT MAINTENANCE ANALYTICS REPORT")
    text_content.append("=" * 50)
    text_content.append("")
    
    # Add timestamp information
    timestamp = json_data.get('timestamp', 'Unknown')
    date = json_data.get('date', 'Unknown')
    text_content.append(f"Report Generated: {timestamp}")
    text_content.append(f"Date: {date}")
    text_content.append(f"Day of Week: {json_data.get('day_of_week', 'Unknown')}")
    text_content.append("")
    
    # Add equipment information
    text_content.append("EQUIPMENT INFORMATION")
    text_content.append("-" * 25)
    equipment_id = json_data.get('equipment_id', 'Unknown')
    equipment_type = json_data.get('equipment_type', 'Unknown')
    text_content.append(f"Equipment ID: {equipment_id}")
    text_content.append(f"Equipment Type: {equipment_type}")
    text_content.append("")
    
    # Add sensor readings
    if 'sensor_readings' in json_data:
        text_content.append("CURRENT SENSOR READINGS")
        text_content.append("-" * 25)
        sensors = json_data['sensor_readings']
        
        for sensor_name, value in sensors.items():
            text_content.append(f"{sensor_name.replace('_', ' ').title()}: {value}")
        text_content.append("")
    
    # Add fault prediction
    if 'fault_prediction' in json_data:
        text_content.append("FAULT PREDICTION ANALYSIS")
        text_content.append("-" * 30)
        prediction = json_data['fault_prediction']
        
        probability = prediction.get('probability', 'Unknown')
        risk_level = prediction.get('risk_level', 'Unknown')
        predicted_failure_date = prediction.get('predicted_failure_date', 'Unknown')
        
        text_content.append(f"Fault Probability: {probability}")
        text_content.append(f"Risk Level: {risk_level}")
        text_content.append(f"Predicted Failure Date: {predicted_failure_date}")
        text_content.append("")
    
    # Add maintenance recommendations
    if 'maintenance_recommendations' in json_data:
        text_content.append("MAINTENANCE RECOMMENDATIONS")
        text_content.append("-" * 35)
        recommendations = json_data['maintenance_recommendations']
        
        priority = recommendations.get('priority', 'Unknown')
        action = recommendations.get('action', 'No action specified')
        estimated_cost = recommendations.get('estimated_cost', 'Unknown')
        
        text_content.append(f"Priority: {priority}")
        text_content.append(f"Recommended Action: {action}")
        text_content.append(f"Estimated Cost: ${estimated_cost}")
        text_content.append("")
    
    # Add detailed analysis
    if 'analysis' in json_data:
        text_content.append("DETAILED ANALYSIS")
        text_content.append("-" * 20)
        analysis = json_data['analysis']
        text_content.append(analysis)
        text_content.append("")
    
    # Add historical context
    if 'historical_context' in json_data:
        text_content.append("HISTORICAL CONTEXT")
        text_content.append("-" * 20)
        context = json_data['historical_context']
        text_content.append(context)
        text_content.append("")
    
    # Add performance metrics
    if 'performance_metrics' in json_data:
        text_content.append("PERFORMANCE METRICS")
        text_content.append("-" * 22)
        metrics = json_data['performance_metrics']
        
        for metric_name, value in metrics.items():
            text_content.append(f"{metric_name.replace('_', ' ').title()}: {value}")
        text_content.append("")
    
    # Add footer
    text_content.append("END OF REPORT")
    text_content.append("=" * 50)
    
    return "\n".join(text_content)

def upload_text_to_s3(text_content, original_key):
    """Upload converted text to S3"""
    config = load_config()
    if not config:
        return False
    
    try:
        s3 = boto3.client('s3', region_name=config['region'])
        
        bucket_name = config['s3']['data_bucket']['name']
        
        # Create text file key
        text_key = original_key.replace('.json', '.txt')
        
        print(f"📤 Uploading text file to s3://{bucket_name}/{text_key}")
        
        s3.put_object(
            Bucket=bucket_name,
            Key=text_key,
            Body=text_content.encode('utf-8'),
            ContentType='text/plain'
        )
        
        print(f"   ✅ Successfully uploaded: {text_key}")
        return text_key
        
    except ClientError as e:
        print(f"❌ Error uploading text: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_additional_sample_texts():
    """Create additional sample maintenance text files"""
    config = load_config()
    if not config:
        return False
    
    try:
        s3 = boto3.client('s3', region_name=config['region'])
        bucket_name = config['s3']['data_bucket']['name']
        prefix = config['s3']['data_bucket']['data_structure']['base_prefix']
        
        # Sample maintenance documents
        sample_docs = [
            {
                "filename": "maintenance_procedures.txt",
                "content": """PREVENTIVE MAINTENANCE PROCEDURES

Equipment Type: Industrial Pumps and Motors

DAILY INSPECTIONS:
- Check for unusual noises, vibrations, or overheating
- Verify proper lubrication levels
- Inspect for leaks or corrosion
- Monitor temperature and pressure readings
- Check electrical connections for tightness

WEEKLY MAINTENANCE:
- Lubricate bearings according to manufacturer specifications
- Clean equipment surfaces and remove debris
- Check belt tension and alignment
- Inspect coupling alignment
- Test emergency shutdown systems

MONTHLY PROCEDURES:
- Perform vibration analysis
- Check motor current and voltage readings
- Inspect and clean cooling systems
- Replace filters as needed
- Document all readings and observations

QUARTERLY MAINTENANCE:
- Comprehensive equipment inspection
- Replace worn components
- Calibrate sensors and instruments
- Update maintenance records
- Schedule major repairs if needed

FAULT INDICATORS:
- Bearing temperature above 180°F indicates potential failure
- Vibration levels exceeding 0.5 inches/second require investigation
- Motor current draw 10% above nameplate indicates problems
- Unusual noise patterns suggest mechanical wear

SAFETY PROCEDURES:
- Always follow lockout/tagout procedures
- Use proper personal protective equipment
- Ensure equipment is properly grounded
- Never bypass safety systems
"""
            },
            {
                "filename": "fault_diagnosis_guide.txt",
                "content": """EQUIPMENT FAULT DIAGNOSIS GUIDE

COMMON FAULT SYMPTOMS AND CAUSES:

EXCESSIVE VIBRATION:
- Misalignment of rotating equipment
- Unbalanced rotating components
- Worn or damaged bearings
- Loose mounting bolts
- Bent or damaged shafts

OVERHEATING:
- Insufficient lubrication
- Blocked cooling passages
- Excessive load conditions
- Poor ventilation
- Electrical problems in motors

UNUSUAL NOISES:
- Grinding sounds indicate bearing wear
- Squealing suggests belt problems
- Knocking indicates loose components
- Humming may indicate electrical issues

PERFORMANCE DEGRADATION:
- Reduced flow rates in pumps
- Decreased efficiency
- Higher energy consumption
- Frequent trips or shutdowns

DIAGNOSTIC PROCEDURES:
1. Visual inspection for obvious problems
2. Temperature measurements using infrared thermometry
3. Vibration analysis using accelerometers
4. Oil analysis for contamination and wear particles
5. Electrical testing for motor-driven equipment

PREDICTIVE MAINTENANCE INDICATORS:
- Trending temperature increases
- Gradual vibration level increases
- Oil analysis showing increasing wear particles
- Decreasing equipment efficiency over time

IMMEDIATE ACTION REQUIRED:
- Equipment temperature above 200°F
- Vibration levels above 1.0 inches/second
- Visible sparking or arcing
- Strong burning odors
- Excessive noise levels
"""
            },
            {
                "filename": "maintenance_best_practices.txt",
                "content": """MAINTENANCE BEST PRACTICES

PLANNING AND SCHEDULING:
- Develop comprehensive maintenance schedules
- Use equipment history to optimize intervals
- Coordinate maintenance with production schedules
- Maintain adequate spare parts inventory
- Plan for seasonal maintenance requirements

CONDITION MONITORING:
- Implement vibration monitoring programs
- Use thermal imaging for early fault detection
- Perform regular oil analysis
- Monitor electrical parameters
- Track equipment performance trends

DOCUMENTATION:
- Maintain detailed maintenance records
- Document all repairs and modifications
- Track failure patterns and root causes
- Keep updated equipment drawings and manuals
- Record all safety incidents and near misses

TRAINING AND COMPETENCY:
- Ensure technicians are properly trained
- Provide ongoing education on new technologies
- Maintain certification requirements
- Cross-train personnel for flexibility
- Document training records

SPARE PARTS MANAGEMENT:
- Maintain critical spare parts inventory
- Use vendor-managed inventory when appropriate
- Implement proper storage conditions
- Track parts usage and lead times
- Establish emergency procurement procedures

SAFETY CONSIDERATIONS:
- Always follow safety procedures
- Use proper tools and equipment
- Maintain clean and organized work areas
- Report all safety hazards immediately
- Conduct regular safety training

CONTINUOUS IMPROVEMENT:
- Analyze failure data for trends
- Implement reliability-centered maintenance
- Use root cause analysis for major failures
- Benchmark against industry standards
- Regularly review and update procedures
"""
            }
        ]
        
        print("📝 Creating additional sample maintenance documents...")
        
        for doc in sample_docs:
            key = f"{prefix}{doc['filename']}"
            
            s3.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=doc['content'].encode('utf-8'),
                ContentType='text/plain'
            )
            
            print(f"   ✅ Created: {doc['filename']}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error creating sample docs: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🔄 Converting JSON data to text format for Knowledge Base...\n")
    
    # Download and convert existing JSON
    json_data, original_key = download_json_data()
    if json_data:
        text_content = convert_to_text(json_data)
        if text_content:
            text_key = upload_text_to_s3(text_content, original_key)
            if text_key:
                print(f"✅ Converted {original_key} to {text_key}")
    
    # Create additional sample documents
    print("\n" + "="*50)
    create_additional_sample_texts()
    
    print("\n" + "="*50)
    print("✅ Text conversion complete!")
    print("\n📋 Next steps:")
    print("1. Trigger Knowledge Base ingestion to process the new text files")
    print("2. Test the Knowledge Base with text-based queries")
    print("3. Verify agent can access the converted data")

if __name__ == "__main__":
    main()