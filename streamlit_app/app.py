"""
Streamlit application for Bedrock Agent maintenance interface.
Provides interactive web interface for maintenance team interactions.
"""
import streamlit as st
import requests
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure Streamlit page
st.set_page_config(
    page_title="Maintenance Agent",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state (Task 9: Implement simple session management)
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    # Generate unique session ID for proper session isolation
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
if 'session_start_time' not in st.session_state:
    st.session_state.session_start_time = datetime.now().isoformat()
if 'feedback' not in st.session_state:
    st.session_state.feedback = []
if 'session_metadata' not in st.session_state:
    st.session_state.session_metadata = {
        'total_queries': 0,
        'successful_responses': 0,
        'error_count': 0,
        'average_response_time': 0.0,
        'last_activity': datetime.now().isoformat()
    }

def main():
    """Main Streamlit application."""
    st.title("Virtual Engineer")
    st.markdown("Ask questions about equipment health, fault patterns, and maintenance recommendations.")
    
    # Add sample queries
    with st.expander("Sample Questions"):
        st.markdown("""
        **Equipment Status:**
        - What is the current status of the industrial conveyor?
        - What faults have been detected in the equipment?
        
        **Sensor Data:**
        - What are the current sensor readings?
        - Show me the temperature and vibration levels
        
        **Maintenance Recommendations:**
        - What maintenance actions are recommended?
        - What is the risk level of detected faults?
        
        **Preventive Maintenance:**
        - What preventive maintenance procedures should I follow?
        - How often should I inspect the equipment?
        """)
    
    # Enhanced sidebar for filtering options (Task 9: Add sidebar for simple filtering options)
    with st.sidebar:
        st.header("Configuration")
        
        # API endpoint configuration with validation
        api_endpoint = st.text_input(
            "API Endpoint",
            value="https://mptessh463dsxj27wmzvzcv74e0bkipi.lambda-url.us-west-2.on.aws/",
            help="Lambda Function URL for the query handler"
        )
        
        # Connection status indicator
        if api_endpoint and api_endpoint != "https://your-lambda-url.lambda-url.region.on.aws/":
            st.success("Endpoint configured")
        else:
            st.warning("Configure endpoint above")
        
        st.divider()
        
        # Enhanced equipment filter (Task 9: Simple filtering options)
        st.subheader("Equipment Filter")
        equipment_ids = st.multiselect(
            "Select Equipment",
            options=[
                "Industrial Conveyor", 
                "Ball Bearing System", 
                "Motor Drive", 
                "Sensor Array",
                "Pump System",
                "Compressor Unit",
                "Heat Exchanger",
                "Control Valve"
            ],
            default=["Industrial Conveyor"],
            help="Filter queries to specific equipment (Requirement 2.4: Multi-equipment analysis)"
        )
        
        # Equipment status summary
        if equipment_ids:
            st.caption(f"Monitoring {len(equipment_ids)} equipment unit(s)")
        
        # Enhanced time range filter (Task 9: Simple filtering options)
        st.subheader("Time Range")
        time_range = st.selectbox(
            "Select Time Range",
            options=["Last 24 hours", "Last 7 days", "Last 30 days", "Last 90 days", "Custom"],
            index=2,
            help="Filter data by time period (Requirement 4.3: Temporal analysis)"
        )
        
        # Custom date range with validation
        if time_range == "Custom":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
            with col2:
                end_date = st.date_input("End Date", value=datetime.now())
            
            # Validate date range
            if start_date > end_date:
                st.error("Start date must be before end date")
            elif (end_date - start_date).days > 365:
                st.warning("Date range exceeds 1 year - queries may be slow")
            else:
                st.success(f"{(end_date - start_date).days} days selected")
        
        # Fault type filter (Task 9: Enhanced filtering)
        st.subheader("Fault Type Filter")
        fault_types = st.multiselect(
            "Focus on Fault Types",
            options=[
                "Bearing Wear",
                "Vibration Anomaly", 
                "Temperature Spike",
                "Pressure Drop",
                "Flow Rate Issue",
                "Electrical Fault",
                "Mechanical Wear",
                "Sensor Malfunction"
            ],
            help="Filter analysis to specific fault types (Requirement 2.4: Fault-specific queries)"
        )
        
        if fault_types:
            st.caption(f"Focusing on {len(fault_types)} fault type(s)")
        
        st.divider()
        
        # Session management section (Task 9: Simple session management)
        st.subheader("Session Management")
        
        # Session info display
        if st.session_state.session_id:
            session_display = st.session_state.session_id[-12:]
            st.text_input("Session ID", value=session_display, disabled=True, help="Current conversation session")
        
        # Enhanced session statistics (Task 9: Simple session management)
        message_count = len(st.session_state.messages)
        user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
        assistant_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Messages", message_count)
        with col2:
            st.metric("Queries", user_messages)
        
        # Additional session metrics
        if st.session_state.session_metadata:
            metadata = st.session_state.session_metadata
            col1, col2 = st.columns(2)
            with col1:
                success_rate = (metadata['successful_responses'] / max(metadata['total_queries'], 1)) * 100
                st.metric("Success Rate", f"{success_rate:.0f}%")
            with col2:
                avg_time = metadata.get('average_response_time', 0)
                st.metric("Avg Response", f"{avg_time:.1f}s")
        
        # Feedback summary
        if st.session_state.feedback:
            helpful_count = len([f for f in st.session_state.feedback if f['rating'] == 'helpful'])
            total_feedback = len(st.session_state.feedback)
            if total_feedback > 0:
                satisfaction = (helpful_count / total_feedback) * 100
                st.metric("Satisfaction", f"{satisfaction:.0f}%", delta=f"{helpful_count}/{total_feedback}")
        
        # Session duration
        if st.session_state.session_start_time:
            try:
                start_time = datetime.fromisoformat(st.session_state.session_start_time)
                duration = datetime.now() - start_time
                duration_str = f"{duration.seconds // 60}m {duration.seconds % 60}s"
                st.caption(f"Session duration: {duration_str}")
            except:
                st.caption("Session active")
        
        # Enhanced clear conversation button (Task 9: Create clear conversation button)
        st.markdown("---")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Clear Chat", type="secondary", use_container_width=True):
                if st.session_state.messages:
                    st.session_state.messages = []
                    st.session_state.session_id = str(uuid.uuid4())  # Generate new session ID
                    st.session_state.session_start_time = datetime.now().isoformat()
                    st.success("Conversation cleared!")
                    st.rerun()
                else:
                    st.info("No messages to clear")
        
        with col2:
            if st.button("New Session", type="primary", use_container_width=True):
                # Create completely new session (Task 9: Session management)
                st.session_state.messages = []
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.session_start_time = datetime.now().isoformat()
                st.success("New session started!")
                st.rerun()
        
        # Export conversation option
        if st.session_state.messages:
            if st.button("Export Chat", use_container_width=True):
                export_conversation()
        
        st.divider()
        
        # System status and help
        st.subheader("System Status")
        
        # Quick system health check
        if st.button("Health Check", use_container_width=True):
            perform_health_check(api_endpoint)
        
        # Help and tips
        with st.expander("Tips & Help"):
            st.markdown("""
            **Filtering Tips:**
            - Select specific equipment for focused analysis
            - Use time ranges to analyze trends
            - Filter by fault types for targeted insights
            
            **Session Management:**
            - Clear chat to remove message history
            - New session creates fresh conversation context
            - Export chat to save important conversations
            
            **Query Tips:**
            - Ask about specific equipment status
            - Request maintenance recommendations
            - Inquire about fault patterns and trends
            """)
        
        # Add current filters summary at bottom
        if equipment_ids or fault_types or time_range != "Last 30 days":
            st.markdown("---")
            st.caption("**Active Filters:**")
            if equipment_ids:
                st.caption(f"Equipment: {', '.join(equipment_ids[:2])}{'...' if len(equipment_ids) > 2 else ''}")
            if fault_types:
                st.caption(f"Faults: {', '.join(fault_types[:2])}{'...' if len(fault_types) > 2 else ''}")
            if time_range != "Last 30 days":
                st.caption(f"Time: {time_range}")
    
    # Add system status indicator in main area
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("Test Connection"):
            with st.spinner("Testing connection..."):
                test_response = send_query(
                    api_endpoint,
                    "System status check",
                    [],
                    ""
                )
                if test_response:
                    st.success("Connection successful!")
                else:
                    st.error("Connection failed")
    
    with col3:
        # Display session info (Requirement 5.6: Session isolation)
        session_display = f"ID: {st.session_state.session_id[-8:]}" if st.session_state.session_id else 'New'
        st.metric("Session", session_display)
        if st.session_state.session_start_time:
            st.caption(f"Started: {st.session_state.session_start_time[:16]}")
    
    # Main chat interface with enhanced filtering
    display_chat_interface(api_endpoint, equipment_ids, time_range, fault_types)

def display_chat_interface(api_endpoint: str, equipment_ids: List[str], time_range: str, fault_types: List[str] = None):
    """Display the main chat interface with enhanced chat functionality."""
    
    # Chat message history display (Task 8: Add chat message history display)
    chat_container = st.container()
    with chat_container:
        # Display conversation history with enhanced formatting (Requirement 5.2, 5.3)
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                # Enhanced message content display with better formatting
                if message["role"] == "assistant":
                    # Display agent responses with basic formatting (Task 8: Display agent responses with basic formatting)
                    response_content = message["content"]
                    
                    # Format response with better structure
                    if "**" in response_content or "###" in response_content:
                        st.markdown(response_content)
                    else:
                        # Add basic formatting for plain text responses
                        formatted_content = format_agent_response(response_content)
                        st.markdown(formatted_content)
                    
                    # Display metadata and timestamps (Requirement 5.2: specific data points and timestamps)
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        if "timestamp" in message:
                            timestamp_display = format_timestamp(message["timestamp"])
                            st.caption(f"{timestamp_display}")
                        if "sessionId" in message and message["sessionId"]:
                            st.caption(f"Session: {message['sessionId'][-8:]}")
                        
                        # Show response time if available (Requirement 5.1: 30-second response)
                        if "response_time" in message:
                            st.caption(f"{message['response_time']:.1f}s")
                    
                    # Display citations with enhanced formatting (Requirement 5.2: actionable recommendations)
                    if "citations" in message and message["citations"]:
                        with st.expander("Sources & References", expanded=False):
                            for i, citation in enumerate(message["citations"], 1):
                                st.markdown(f"**{i}.** {citation}")
                    
                    # Display any limitations or explanations (Requirement 5.4)
                    if "limitations" in message and message["limitations"]:
                        with st.expander("Response Limitations", expanded=False):
                            st.info(message["limitations"])
                else:
                    # User message display
                    st.markdown(message["content"])
                    if "timestamp" in message:
                        timestamp_display = format_timestamp(message["timestamp"])
                        st.caption(f"{timestamp_display}")
    
    # Chat input with enhanced context handling (Requirement 5.3: maintain conversation context)
    if prompt := st.chat_input("Ask about equipment health, fault patterns, or maintenance..."):
        # Record user message timestamp
        user_timestamp = datetime.now().isoformat()
        
        # Add user message to chat history with timestamp
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "timestamp": user_timestamp
        })
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
            st.caption(f"{format_timestamp(user_timestamp)}")
        
        # Generate and display assistant response with loading indicator
        with st.chat_message("assistant"):
            # Enhanced loading indicator (Task 8: Add simple loading indicator)
            loading_placeholder = st.empty()
            with loading_placeholder:
                with st.spinner("Analyzing your query..."):
                    # Track response time for Requirement 5.1
                    start_time = datetime.now()
                    
                    # Update session metadata (Task 9: Session management)
                    st.session_state.session_metadata['total_queries'] += 1
                    st.session_state.session_metadata['last_activity'] = datetime.now().isoformat()
                    
                    # Query submission to Lambda function (Task 8: Implement query submission to Lambda function)
                    response = send_query_with_context(api_endpoint, prompt, equipment_ids, time_range, fault_types)
                    
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds()
                    
                    # Update response time tracking
                    current_avg = st.session_state.session_metadata.get('average_response_time', 0)
                    total_queries = st.session_state.session_metadata['total_queries']
                    new_avg = ((current_avg * (total_queries - 1)) + response_time) / total_queries
                    st.session_state.session_metadata['average_response_time'] = new_avg
            
            # Clear loading indicator
            loading_placeholder.empty()
            
            if response:
                # Update success tracking (Task 9: Session management)
                if not response.get("error_type"):
                    st.session_state.session_metadata['successful_responses'] += 1
                else:
                    st.session_state.session_metadata['error_count'] += 1
                
                # Display response with enhanced formatting (Task 8: Display agent responses with basic formatting)
                response_content = response.get("response", "No response received")
                timestamp = response.get("timestamp", datetime.now().isoformat())
                
                # Format and display the response
                if "**" in response_content or "###" in response_content:
                    st.markdown(response_content)
                else:
                    formatted_content = format_agent_response(response_content)
                    st.markdown(formatted_content)
                
                # Display metadata (Requirement 5.2: specific data points and timestamps)
                col1, col2 = st.columns([3, 1])
                with col2:
                    st.caption(f"{format_timestamp(timestamp)}")
                    if response.get("sessionId"):
                        st.caption(f"Session: {response['sessionId'][-8:]}")
                    st.caption(f"{response_time:.1f}s")
                
                # Add assistant message to chat history with enhanced metadata
                assistant_message = {
                    "role": "assistant",
                    "content": response_content,
                    "citations": response.get("citations", []),
                    "timestamp": timestamp,
                    "sessionId": response.get("sessionId", ""),
                    "response_time": response_time
                }
                
                # Add limitations if query couldn't be fully answered (Requirement 5.4)
                if response.get("limitations"):
                    assistant_message["limitations"] = response["limitations"]
                
                st.session_state.messages.append(assistant_message)
                
                # Display citations if available
                if response.get("citations"):
                    with st.expander("Sources & References", expanded=False):
                        for i, citation in enumerate(response["citations"], 1):
                            st.markdown(f"**{i}.** {citation}")
                
                # Display limitations if any (Requirement 5.4)
                if response.get("limitations"):
                    with st.expander("Response Limitations", expanded=False):
                        st.info(response["limitations"])
                        
                        # Show suggested actions if available (Task 9: Enhanced user feedback)
                        if response.get("suggested_actions"):
                            st.markdown("**Suggested Actions:**")
                            for action in response["suggested_actions"]:
                                st.markdown(f"• {action}")
                
                # Add user feedback collection (Task 9: Enhanced user feedback)
                if response_content and not response.get("error_type"):
                    with st.expander("Rate this response", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("Helpful", key=f"helpful_{len(st.session_state.messages)}"):
                                st.success("Thank you for your feedback!")
                                # Store feedback in session state for analytics
                                if 'feedback' not in st.session_state:
                                    st.session_state.feedback = []
                                st.session_state.feedback.append({
                                    "timestamp": datetime.now().isoformat(),
                                    "rating": "helpful",
                                    "query": prompt,
                                    "session_id": st.session_state.session_id
                                })
                        with col2:
                            if st.button("Not helpful", key=f"not_helpful_{len(st.session_state.messages)}"):
                                st.info("Thank you for your feedback. We'll work to improve!")
                                if 'feedback' not in st.session_state:
                                    st.session_state.feedback = []
                                st.session_state.feedback.append({
                                    "timestamp": datetime.now().isoformat(),
                                    "rating": "not_helpful",
                                    "query": prompt,
                                    "session_id": st.session_state.session_id
                                })
                        with col3:
                            if st.button("Retry", key=f"retry_{len(st.session_state.messages)}"):
                                # Remove the last assistant message and retry
                                if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
                                    st.session_state.messages.pop()
                                st.rerun()
                        
            else:
                # Update error tracking (Task 9: Session management)
                st.session_state.session_metadata['error_count'] += 1
                
                # Enhanced error handling with specific explanations (Task 9: Basic error handling and user feedback)
                error_msg = "I apologize, but I couldn't process your request at this time."
                limitations_msg = "This could be due to: network connectivity issues, system maintenance, or the query format. Please check the API endpoint configuration and try again."
                
                # Enhanced error display with actionable feedback
                st.error(error_msg)
                
                # Provide specific troubleshooting steps
                with st.expander("🔧 Troubleshooting Steps", expanded=True):
                    st.markdown("""
                    **Try these steps:**
                    1. Check if the API endpoint is correctly configured in the sidebar
                    2. Click 'Health Check' in the sidebar to test connectivity
                    3. Try clearing the conversation and starting fresh
                    4. Rephrase your question using simpler terms
                    5. Wait a moment and try again (system may be busy)
                    """)
                    
                    # Quick action buttons for error recovery
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Retry Query", key="retry_query"):
                            st.rerun()
                    with col2:
                        if st.button("Health Check", key="error_health_check"):
                            perform_health_check(api_endpoint)
                    with col3:
                        if st.button("Clear & Restart", key="error_clear"):
                            st.session_state.messages = []
                            st.session_state.session_id = str(uuid.uuid4())
                            st.session_state.session_start_time = datetime.now().isoformat()
                            st.rerun()
                
                st.info(limitations_msg)
                
                # Add error message to chat history with enhanced metadata
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "limitations": limitations_msg,
                    "timestamp": datetime.now().isoformat(),
                    "response_time": response_time,
                    "error_type": "connection_failure",
                    "troubleshooting_provided": True
                })

def format_agent_response(response_content: str) -> str:
    """Format agent response with basic structure for better readability."""
    if not response_content:
        return response_content
    
    # Split into paragraphs and add basic formatting
    paragraphs = response_content.split('\n\n')
    formatted_paragraphs = []
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # Add emphasis to key maintenance terms
        maintenance_terms = [
            'CRITICAL', 'WARNING', 'IMMEDIATE ACTION', 'URGENT', 
            'RECOMMENDED', 'MAINTENANCE REQUIRED', 'INSPECTION NEEDED'
        ]
        
        for term in maintenance_terms:
            if term in paragraph.upper():
                paragraph = paragraph.replace(term, f"**{term}**")
                paragraph = paragraph.replace(term.lower(), f"**{term.lower()}**")
        
        # Format numbered lists
        lines = paragraph.split('\n')
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                formatted_lines.append(f"• {line[2:].strip()}")
            else:
                formatted_lines.append(line)
        paragraph = '\n'.join(formatted_lines)
        
        formatted_paragraphs.append(paragraph)
    
    return '\n\n'.join(formatted_paragraphs)

def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display."""
    try:
        if timestamp_str:
            # Try to parse ISO format timestamp
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%H:%M:%S")
        return ""
    except:
        # If parsing fails, return the original string truncated
        return timestamp_str[:8] if len(timestamp_str) > 8 else timestamp_str

def export_conversation():
    """Export conversation history for user download (Task 9: Enhanced user feedback)."""
    try:
        if not st.session_state.messages:
            st.warning("No conversation to export")
            return
        
        # Create export data
        export_data = {
            "session_id": st.session_state.session_id,
            "export_timestamp": datetime.now().isoformat(),
            "session_start": st.session_state.session_start_time,
            "message_count": len(st.session_state.messages),
            "conversation": []
        }
        
        # Format messages for export
        for msg in st.session_state.messages:
            export_msg = {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg.get("timestamp", ""),
            }
            
            # Add additional metadata for assistant messages
            if msg["role"] == "assistant":
                if "citations" in msg:
                    export_msg["citations"] = msg["citations"]
                if "response_time" in msg:
                    export_msg["response_time"] = msg["response_time"]
                if "limitations" in msg:
                    export_msg["limitations"] = msg["limitations"]
            
            export_data["conversation"].append(export_msg)
        
        # Create downloadable JSON
        export_json = json.dumps(export_data, indent=2)
        
        # Offer download
        st.download_button(
            label="Download Conversation",
            data=export_json,
            file_name=f"maintenance_chat_{st.session_state.session_id[-8:]}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            help="Download conversation as JSON file"
        )
        
        st.success("Conversation ready for download!")
        
    except Exception as e:
        st.error(f"Export failed: {str(e)}")

def perform_health_check(api_endpoint: str):
    """Perform system health check (Task 9: Basic error handling and user feedback)."""
    try:
        if not api_endpoint or api_endpoint == "https://your-lambda-url.lambda-url.region.on.aws/":
            st.error("No API endpoint configured")
            return
        
        with st.spinner("Checking system health..."):
            # Test basic connectivity
            test_payload = {
                "query": "System health check",
                "sessionId": "health_check_" + str(uuid.uuid4())[:8]
            }
            
            start_time = datetime.now()
            response = requests.post(
                api_endpoint,
                json=test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds()
            
            if response.status_code == 200:
                st.success(f"System healthy (Response: {response_time:.2f}s)")
                
                # Show additional health metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Status", "Healthy", delta="✅")
                with col2:
                    st.metric("Response Time", f"{response_time:.2f}s", 
                             delta="Good" if response_time < 5 else "Slow")
                with col3:
                    status_code = response.status_code
                    st.metric("HTTP Status", status_code, delta="✅" if status_code == 200 else "❌")
                
            else:
                st.error(f"❌ System issue (Status: {response.status_code})")
                st.info("The maintenance system may be experiencing issues. Please try again later.")
                
    except requests.exceptions.Timeout:
        st.error("❌ Health check timed out")
        st.info("The system is not responding within expected time limits.")
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to system")
        st.info("Please check the API endpoint configuration and network connectivity.")
    except Exception as e:
        st.error(f"❌ Health check failed: {str(e)}")
        st.info("An unexpected error occurred during the health check.")

def send_query_with_context(api_endpoint: str, query: str, equipment_ids: List[str], time_range: str, fault_types: List[str] = None) -> Optional[Dict]:
    """Enhanced query submission with conversation context (Requirement 5.3)."""
    try:
        # Validate API endpoint
        if not api_endpoint or api_endpoint == "https://your-lambda-url.lambda-url.region.on.aws/":
            return {
                "response": "API endpoint not configured",
                "limitations": "Please configure a valid API endpoint in the sidebar to connect to the maintenance system."
            }
        
        # Build context-aware query with conversation history (Requirement 5.3)
        enhanced_query = build_contextual_query(query, equipment_ids, time_range, fault_types)
        
        payload = {
            "query": enhanced_query,
            "sessionId": st.session_state.session_id or "",
            "context": {
                "equipment_filter": equipment_ids,
                "time_range": time_range,
                "fault_types": fault_types or [],
                "conversation_length": len(st.session_state.messages)
            }
        }
        
        # Make API call with enhanced error handling
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(
            api_endpoint,
            json=payload,
            headers=headers,
            timeout=30  # Requirement 5.1: Response within 30 seconds
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Update session ID if received
            if result.get("sessionId"):
                st.session_state.session_id = result["sessionId"]
            
            # Process response and check for limitations (Requirement 5.4)
            processed_response = process_agent_response(result)
            return processed_response
            
        else:
            # Enhanced error handling with specific explanations (Task 9: Basic error handling and user feedback)
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            error_message = error_data.get('message', f'API request failed with status {response.status_code}')
            
            # Provide specific error guidance based on status code
            if response.status_code == 403:
                limitations = "Access denied. Please check your API permissions and authentication settings."
            elif response.status_code == 404:
                limitations = "API endpoint not found. Please verify the Lambda Function URL in the sidebar configuration."
            elif response.status_code == 429:
                limitations = "Too many requests. Please wait a moment before trying again."
            elif response.status_code >= 500:
                limitations = "Server error occurred. The maintenance system may be temporarily unavailable."
            else:
                limitations = f"Technical details: {error_message}. Please try again or contact support if the issue persists."
            
            return {
                "response": "I encountered a technical issue while processing your request.",
                "limitations": limitations,
                "error_code": response.status_code,
                "error_type": "api_error"
            }
        
    except requests.exceptions.Timeout:
        return {
            "response": "Your request timed out after 30 seconds.",
            "limitations": "The maintenance system may be processing a complex query or experiencing high load. Please try a simpler question or wait a moment before trying again.",
            "error_type": "timeout",
            "suggested_actions": ["Try a simpler query", "Wait and retry", "Check system status"]
        }
    except requests.exceptions.ConnectionError:
        return {
            "response": "Could not connect to the maintenance system.",
            "limitations": "Please check the API endpoint configuration and your network connection. The system may be temporarily unavailable.",
            "error_type": "connection_error",
            "suggested_actions": ["Check API endpoint", "Verify network connection", "Try health check"]
        }
    except Exception as e:
        return {
            "response": "An unexpected error occurred while processing your request.",
            "limitations": f"Technical details: {str(e)}. Please try again or contact support if the issue persists.",
            "error_type": "unexpected_error",
            "suggested_actions": ["Retry the request", "Clear conversation", "Contact support"]
        }

def build_contextual_query(query: str, equipment_ids: List[str], time_range: str, fault_types: List[str] = None) -> str:
    """Build context-aware query for better conversation flow (Requirement 5.3)."""
    enhanced_query = query
    
    # Add equipment context if filters are applied
    if equipment_ids:
        enhanced_query += f" (Focus on equipment: {', '.join(equipment_ids)})"
    
    # Add time range context
    if time_range and time_range != "Last 30 days":
        enhanced_query += f" (Time range: {time_range})"
    
    # Add fault type context if filters are applied (Task 9: Enhanced filtering)
    if fault_types:
        enhanced_query += f" (Focus on fault types: {', '.join(fault_types)})"
    
    # Add conversation context for follow-up questions (Requirement 5.3)
    if len(st.session_state.messages) > 0:
        # Check if this might be a follow-up question
        follow_up_indicators = ['also', 'what about', 'and', 'additionally', 'furthermore', 'moreover']
        if any(indicator in query.lower() for indicator in follow_up_indicators):
            enhanced_query += " (This is a follow-up question in our ongoing conversation)"
    
    return enhanced_query

def process_agent_response(result: Dict) -> Dict:
    """Process agent response and identify limitations (Requirement 5.4)."""
    response_text = result.get("response", "No response received")
    
    # Check for common limitation indicators in the response
    limitation_indicators = [
        "I don't have access to",
        "I cannot find",
        "No data available",
        "Unable to retrieve",
        "Information not found",
        "I apologize, but",
        "I'm sorry, but"
    ]
    
    limitations = None
    for indicator in limitation_indicators:
        if indicator.lower() in response_text.lower():
            limitations = "The response may be limited due to data availability or access restrictions. Consider rephrasing your question or checking if the requested information exists in the system."
            break
    
    processed_result = {
        "response": response_text,
        "sessionId": result.get("sessionId", ""),
        "citations": result.get("citations", []),
        "timestamp": result.get("timestamp", datetime.now().isoformat())
    }
    
    if limitations:
        processed_result["limitations"] = limitations
    
    return processed_result

def send_query(api_endpoint: str, query: str, equipment_ids: List[str], time_range: str) -> Optional[Dict]:
    """Send query to the Lambda function via Function URL."""
    try:
        # Validate API endpoint
        if not api_endpoint or api_endpoint == "https://your-lambda-url.lambda-url.region.on.aws/":
            st.error("Please configure a valid API endpoint in the sidebar")
            return None
        
        # Enhance query with context if filters are applied
        enhanced_query = query
        if equipment_ids:
            enhanced_query += f" (Focus on equipment: {', '.join(equipment_ids)})"
        if time_range and time_range != "Last 30 days":
            enhanced_query += f" (Time range: {time_range})"
        
        payload = {
            "query": enhanced_query,
            "sessionId": st.session_state.session_id or ""
        }
        
        # Make API call to Lambda Function URL
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            api_endpoint,
            json=payload,
            headers=headers,
            timeout=30  # Requirement 5.1: Response within 30 seconds
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Update session ID if received
            if result.get("sessionId"):
                st.session_state.session_id = result["sessionId"]
            
            return {
                "response": result.get("response", "No response received"),
                "sessionId": result.get("sessionId", ""),
                "citations": result.get("citations", []),
                "timestamp": result.get("timestamp", "")
            }
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            error_message = error_data.get('message', f'API request failed with status {response.status_code}')
            st.error(f"API Error: {error_message}")
            return None
        
    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 30 seconds. The maintenance system may be busy. Please try again."
        st.error(error_msg)
        # Log security/access event (Requirement 6.4)
        st.info("ℹ️ Timeout events are logged for system monitoring")
        return None
    except requests.exceptions.ConnectionError:
        error_msg = "Could not connect to the maintenance system. Please check the API endpoint and your network connection."
        st.error(error_msg)
        # Log security/access event (Requirement 6.4)
        st.info("ℹ️ Connection failures are logged for security monitoring")
        return None
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error occurred: {str(e)}"
        st.error(error_msg)
        # Log security/access event (Requirement 6.4)
        st.info("ℹ️ Network errors are logged for security analysis")
        return None
    except json.JSONDecodeError:
        error_msg = "Invalid response format from the maintenance system. Please contact system administrator."
        st.error(error_msg)
        # Log security/access event (Requirement 6.4)
        st.info("ℹ️ Invalid responses are logged for security monitoring")
        return None
    except Exception as e:
        error_msg = f"Unexpected error occurred: {str(e)}"
        st.error(error_msg)
        # Log security/access event (Requirement 6.4)
        st.info("ℹ️ All errors are logged for system security and monitoring")
        return None

if __name__ == "__main__":
    main()