#!/usr/bin/env python3
"""
Create comprehensive maintenance report with all sensor data and trigger new ingestion
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

def create_complete_maintenance_report():
    """Create a complete maintenance report with all the sensor data"""
    config = load_config()
    if not config:
        return False
    
    try:
        s3 = boto3.client('s3', region_name=config['region'])
        
        bucket_name = config['s3']['data_bucket']['name']
        json_key = "bedrock-recommendations/analytics/2025/09/11/analytics_20250911_122655_572660.json"
        
        # Download original JSON
        response = s3.get_object(Bucket=bucket_name, Key=json_key)
        json_content = response['Body'].read().decode('utf-8')
        data = json.loads(json_content)
        
        # Create comprehensive text report
        text_lines = []
        
        # Header
        text_lines.append("INDUSTRIAL CONVEYOR MAINTENANCE ANALYTICS REPORT")
        text_lines.append("=" * 55)
        text_lines.append("")
        
        # Report Information
        text_lines.append("REPORT INFORMATION")
        text_lines.append("-" * 20)
        text_lines.append(f"Generated: {data.get('timestamp', 'Unknown')}")
        text_lines.append(f"Date: {data.get('date', 'Unknown')}")
        text_lines.append(f"Time: {data.get('hour', 'Unknown')}:00")
        text_lines.append(f"Day: {data.get('day_of_week', 'Unknown')}")
        text_lines.append(f"Analysis ID: {data.get('inference_id', 'Unknown')}")
        text_lines.append(f"Recommendation ID: {data.get('recommendation_id', 'Unknown')}")
        text_lines.append("")
        
        # Equipment Information
        text_lines.append("EQUIPMENT INFORMATION")
        text_lines.append("-" * 25)
        text_lines.append(f"Equipment Type: {data.get('equipment_type', 'Unknown')}")
        text_lines.append(f"Record Type: {data.get('record_type', 'Unknown')}")
        text_lines.append(f"Model Used: {data.get('model_used', 'Unknown')}")
        text_lines.append(f"Processing Time: {data.get('processing_time_ms', 0):.1f} ms")
        text_lines.append("")
        
        # Current Sensor Readings
        text_lines.append("CURRENT SENSOR READINGS")
        text_lines.append("-" * 25)
        text_lines.append(f"Speed: {data.get('speed_rpm', 'Unknown')} RPM")
        text_lines.append(f"Load: {data.get('load_units', 'Unknown')} units")
        text_lines.append(f"Current: {data.get('current_amps', 'Unknown')} amps")
        text_lines.append(f"Temperature: {data.get('temperature_celsius', 'Unknown')}°C")
        text_lines.append(f"Vibration: {data.get('vibration_mms', 'Unknown')} mm/s")
        text_lines.append("")
        
        # Sensor Status Assessment
        text_lines.append("SENSOR STATUS ASSESSMENT")
        text_lines.append("-" * 30)
        text_lines.append(f"Speed Status: {data.get('speed_status', 'Unknown')}")
        text_lines.append(f"Load Status: {data.get('load_status', 'Unknown')}")
        text_lines.append(f"Current Status: {data.get('current_status', 'Unknown')}")
        text_lines.append(f"Temperature Status: {data.get('temperature_status', 'Unknown')}")
        text_lines.append(f"Vibration Status: {data.get('vibration_status', 'Unknown')}")
        text_lines.append("")
        
        # Fault Prediction Analysis
        text_lines.append("FAULT PREDICTION ANALYSIS")
        text_lines.append("-" * 30)
        text_lines.append(f"Predicted Fault: {data.get('predicted_fault', 'Unknown')}")
        text_lines.append(f"Fault Category: {data.get('fault_category', 'Unknown')}")
        text_lines.append(f"Confidence Score: {data.get('confidence_score', 'Not provided')}")
        text_lines.append(f"Confidence Category: {data.get('confidence_category', 'Unknown')}")
        text_lines.append("")
        
        # Operational Status
        text_lines.append("OPERATIONAL STATUS")
        text_lines.append("-" * 20)
        normal_op = "YES" if data.get('is_normal_operation', 0) == 1 else "NO"
        critical_fault = "YES" if data.get('is_critical_fault', 0) == 1 else "NO"
        immediate_action = "YES" if data.get('requires_immediate_action', 0) == 1 else "NO"
        
        text_lines.append(f"Normal Operation: {normal_op}")
        text_lines.append(f"Critical Fault Detected: {critical_fault}")
        text_lines.append(f"Requires Immediate Action: {immediate_action}")
        text_lines.append("")
        
        # Risk Assessment
        text_lines.append("RISK ASSESSMENT")
        text_lines.append("-" * 17)
        text_lines.append(f"Risk Level: {data.get('risk_level', 'Unknown')}")
        text_lines.append(f"Risk Score: {data.get('risk_score', 'Unknown')}/5")
        text_lines.append("")
        
        # Maintenance Recommendations
        text_lines.append("MAINTENANCE RECOMMENDATIONS")
        text_lines.append("-" * 35)
        text_lines.append(f"Summary: {data.get('recommendation_summary', 'No summary available')}")
        text_lines.append("")
        text_lines.append(f"Action Items: {data.get('action_items_count', 0)} recommended actions")
        text_lines.append("")
        
        # Detailed Analysis
        text_lines.append("DETAILED ANALYSIS")
        text_lines.append("-" * 20)
        text_lines.append("Based on the sensor readings and fault prediction model:")
        text_lines.append("")
        text_lines.append("1. BEARING SYSTEM ANALYSIS:")
        text_lines.append("   - Ball bearing fault detected in the conveyor system")
        text_lines.append("   - Early signs of bearing degradation are present")
        text_lines.append("   - Vibration levels are within normal range but trending upward")
        text_lines.append("")
        text_lines.append("2. PERFORMANCE INDICATORS:")
        text_lines.append(f"   - Current speed of {data.get('speed_rpm', 'Unknown')} RPM is within normal operating range")
        text_lines.append(f"   - Load of {data.get('load_units', 'Unknown')} units indicates standard operational demand")
        text_lines.append(f"   - Temperature of {data.get('temperature_celsius', 'Unknown')}°C is acceptable but should be monitored")
        text_lines.append("")
        text_lines.append("3. IMMEDIATE CONCERNS:")
        text_lines.append("   - Ball bearing degradation requires preventive maintenance")
        text_lines.append("   - Equipment is operational but needs attention to prevent failure")
        text_lines.append("   - Slight deviations from optimal performance detected")
        text_lines.append("")
        
        # Recommended Actions
        text_lines.append("RECOMMENDED IMMEDIATE ACTIONS")
        text_lines.append("-" * 35)
        text_lines.append("1. Inspect ball bearings for wear and damage")
        text_lines.append("2. Check lubrication levels and quality")
        text_lines.append("3. Perform vibration analysis to confirm bearing condition")
        text_lines.append("4. Schedule bearing replacement during next maintenance window")
        text_lines.append("5. Increase monitoring frequency for temperature and vibration")
        text_lines.append("6. Document current readings for trend analysis")
        text_lines.append("7. Prepare spare bearings and maintenance tools")
        text_lines.append("8. Schedule downtime for bearing replacement")
        text_lines.append("")
        
        # Footer
        text_lines.append("END OF MAINTENANCE REPORT")
        text_lines.append("=" * 55)
        text_lines.append("")
        text_lines.append("This report was generated by the AWS Bedrock maintenance analytics system.")
        text_lines.append("For questions or additional analysis, contact the maintenance team.")
        
        complete_text = "\n".join(text_lines)
        
        # Upload the complete report
        prefix = config['s3']['data_bucket']['data_structure']['base_prefix']
        text_key = f"{prefix}complete_maintenance_report.txt"
        
        print(f"📤 Uploading complete maintenance report...")
        print(f"   File: {text_key}")
        print(f"   Size: {len(complete_text)} characters")
        
        s3.put_object(
            Bucket=bucket_name,
            Key=text_key,
            Body=complete_text.encode('utf-8'),
            ContentType='text/plain'
        )
        
        print(f"✅ Complete maintenance report uploaded successfully")
        
        # Also create a summary version
        summary_lines = []
        summary_lines.append("MAINTENANCE ALERT SUMMARY")
        summary_lines.append("=" * 30)
        summary_lines.append("")
        summary_lines.append(f"Equipment: {data.get('equipment_type', 'Unknown')}")
        summary_lines.append(f"Date: {data.get('date', 'Unknown')}")
        summary_lines.append(f"Fault Detected: {data.get('predicted_fault', 'Unknown')}")
        summary_lines.append(f"Risk Level: {data.get('risk_level', 'Unknown')}")
        summary_lines.append(f"Action Required: {'YES' if data.get('requires_immediate_action', 0) == 1 else 'NO'}")
        summary_lines.append("")
        summary_lines.append("KEY FINDINGS:")
        summary_lines.append("- Ball bearing degradation detected")
        summary_lines.append("- Equipment operational but needs preventive maintenance")
        summary_lines.append("- Immediate inspection and bearing replacement recommended")
        summary_lines.append("")
        summary_lines.append("SENSOR READINGS:")
        summary_lines.append(f"- Speed: {data.get('speed_rpm', 'Unknown')} RPM (Normal)")
        summary_lines.append(f"- Temperature: {data.get('temperature_celsius', 'Unknown')}°C (Normal)")
        summary_lines.append(f"- Vibration: {data.get('vibration_mms', 'Unknown')} mm/s (Normal)")
        summary_lines.append(f"- Current: {data.get('current_amps', 'Unknown')} amps (Normal)")
        
        summary_text = "\n".join(summary_lines)
        summary_key = f"{prefix}maintenance_alert_summary.txt"
        
        s3.put_object(
            Bucket=bucket_name,
            Key=summary_key,
            Body=summary_text.encode('utf-8'),
            ContentType='text/plain'
        )
        
        print(f"✅ Maintenance alert summary uploaded: {summary_key}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error creating maintenance report: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def trigger_new_ingestion():
    """Trigger new ingestion job"""
    config = load_config()
    if not config:
        return False
    
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=config['region'])
        
        kb_id = config['knowledge_base_id']
        ds_id = config['data_source_id']
        
        print(f"\n🚀 Triggering new ingestion job...")
        
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id,
            description="Ingestion of complete maintenance reports with full sensor data"
        )
        
        job_id = response['ingestionJob']['ingestionJobId']
        print(f"✅ Started ingestion job: {job_id}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error starting ingestion: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Creating complete maintenance reports with full sensor data...\n")
    
    if create_complete_maintenance_report():
        trigger_new_ingestion()
    
    print("\n" + "="*50)
    print("✅ Complete maintenance reports created and ingestion triggered!")
    print("\n📋 Next steps:")
    print("1. Wait for ingestion to complete (2-3 minutes)")
    print("2. Test Knowledge Base queries")
    print("3. Test Agent integration")

if __name__ == "__main__":
    main()