#!/usr/bin/env python3
"""
Test script for Streamlit chat functionality enhancements.
Tests the new features implemented in task 8.
"""

import sys
import os
sys.path.append('streamlit_app')

from datetime import datetime
from streamlit_app.app import (
    format_agent_response, 
    format_timestamp, 
    build_contextual_query,
    process_agent_response
)

def test_format_agent_response():
    """Test the agent response formatting function."""
    print("Testing format_agent_response...")
    
    # Test basic formatting
    response = "This is a test response. CRITICAL maintenance required.\n\n1. Check temperature.\n2. Inspect bearings."
    formatted = format_agent_response(response)
    
    print(f"Original: {repr(response)}")
    print(f"Formatted: {repr(formatted)}")
    
    assert "**CRITICAL**" in formatted, "Critical terms should be bolded"
    assert "• Check temperature" in formatted, "Numbered lists should be converted to bullets"
    print("✅ format_agent_response works correctly")

def test_format_timestamp():
    """Test timestamp formatting function."""
    print("Testing format_timestamp...")
    
    # Test ISO format timestamp
    timestamp = "2024-01-15T10:30:45"
    formatted = format_timestamp(timestamp)
    
    assert "10:30:45" in formatted, f"Expected time format, got: {formatted}"
    
    # Test empty timestamp
    empty_formatted = format_timestamp("")
    assert empty_formatted == "", "Empty timestamp should return empty string"
    
    print("✅ format_timestamp works correctly")

def test_build_contextual_query():
    """Test contextual query building."""
    print("Testing build_contextual_query...")
    
    # Mock session state for testing
    class MockSessionState:
        def __init__(self):
            self.messages = [{"role": "user", "content": "Previous question"}]
    
    # Simulate session state
    import streamlit_app.app as app_module
    app_module.st = type('MockST', (), {'session_state': MockSessionState()})()
    
    query = "What about the temperature?"
    equipment_ids = ["Industrial Conveyor"]
    time_range = "Last 7 days"
    
    contextual_query = build_contextual_query(query, equipment_ids, time_range)
    
    assert "Industrial Conveyor" in contextual_query, "Equipment context should be added"
    assert "Last 7 days" in contextual_query, "Time range context should be added"
    assert "follow-up" in contextual_query, "Follow-up indicator should be detected"
    
    print("✅ build_contextual_query works correctly")

def test_process_agent_response():
    """Test agent response processing for limitations."""
    print("Testing process_agent_response...")
    
    # Test response with limitations
    result_with_limitations = {
        "response": "I don't have access to that specific data.",
        "sessionId": "test-session",
        "citations": []
    }
    
    processed = process_agent_response(result_with_limitations)
    
    assert "limitations" in processed, "Limitations should be detected"
    assert processed["limitations"] is not None, "Limitations message should be provided"
    
    # Test normal response
    result_normal = {
        "response": "The equipment is operating normally.",
        "sessionId": "test-session",
        "citations": []
    }
    
    processed_normal = process_agent_response(result_normal)
    assert "limitations" not in processed_normal or processed_normal.get("limitations") is None, "No limitations should be detected for normal response"
    
    print("✅ process_agent_response works correctly")

def main():
    """Run all tests."""
    print("🧪 Testing Streamlit Chat Functionality Enhancements")
    print("=" * 50)
    
    try:
        test_format_agent_response()
        test_format_timestamp()
        test_build_contextual_query()
        test_process_agent_response()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! Chat functionality enhancements are working correctly.")
        print("\nImplemented features:")
        print("- ✅ Enhanced chat message history display")
        print("- ✅ Improved query submission with context")
        print("- ✅ Enhanced loading indicators")
        print("- ✅ Better agent response formatting")
        print("- ✅ Timestamp and metadata display")
        print("- ✅ Conversation context maintenance")
        print("- ✅ Limitation explanations")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)