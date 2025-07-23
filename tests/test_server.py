"""
Tests for the Flask server endpoints.
"""

import unittest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server.app import app


class TestServerEndpoints(unittest.TestCase):
    """Test cases for the Flask server endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = app.test_client()
        self.app.testing = True
        
        self.sample_call_data = {
            "call": {
                "call_id": "test_call_123",
                "from_number": "+15551234567",
                "call_status": "ended",
                "start_timestamp": 1640995200000,  # 2022-01-01 00:00:00 UTC
                "end_timestamp": 1640995260000,    # 2022-01-01 00:01:00 UTC
                "duration_ms": 60000,
                "transcript": "User: Hello\nAgent: Hi, how can I help you?",
                "call_analysis": {
                    "call_summary": "Customer called for support",
                    "custom_analysis_data": {
                        "name_of_caller": "John Doe",
                        "email_to_reach": "john@example.com"
                    }
                }
            }
        }
        
        self.sample_ticket_data = {
            "subject": "Test Ticket",
            "description": "Test description",
            "requester_phone": "+15551234567",
            "tags": ["test", "voice-call"],
            "public": False
        }
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = self.app.get('/health')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'zendesk-voice-server')
        self.assertIn('timestamp', data)
    
    @patch('server.app.processed_calls_ref')
    @patch('server.app.ZendeskAPI')
    def test_call_events_manager_success(self, mock_zendesk_class, mock_firebase_ref):
        """Test successful call event processing."""
        # Mock Firebase to return no existing call
        mock_firebase_instance = Mock()
        mock_firebase_ref.child.return_value.get.return_value = None
        mock_firebase_ref.child.return_value.set.return_value = None
        
        # Mock Zendesk API
        mock_zendesk_instance = Mock()
        mock_zendesk_class.return_value = mock_zendesk_instance
        mock_zendesk_instance.create_ticket.return_value = {
            "ticket": {
                "id": 12345,
                "subject": "Test Ticket",
                "status": "open"
            }
        }
        
        response = self.app.post(
            '/call_events_manager',
            data=json.dumps(self.sample_call_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['ticket_id'], 12345)
    
    @patch('server.app.processed_calls_ref')
    def test_call_events_manager_already_processed(self, mock_firebase_ref):
        """Test call event processing for already processed call."""
        # Mock Firebase to return existing call
        mock_firebase_instance = Mock()
        mock_firebase_ref.child.return_value.get.return_value = {
            "ticket_id": 12345,
            "processed_at": "2022-01-01T00:00:00"
        }
        
        response = self.app.post(
            '/call_events_manager',
            data=json.dumps(self.sample_call_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Call already processed')
    
    def test_call_events_manager_no_data(self):
        """Test call event processing with no data."""
        response = self.app.post(
            '/call_events_manager',
            data='',
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)
    
    def test_call_events_manager_missing_required_fields(self):
        """Test call event processing with missing required fields."""
        incomplete_data = {
            "call": {
                "call_id": "test_call_123"
                # Missing from_number and call_status
            }
        }
        
        response = self.app.post(
            '/call_events_manager',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)
    
    def test_call_events_manager_call_not_ended(self):
        """Test call event processing for call that hasn't ended."""
        call_data = self.sample_call_data.copy()
        call_data['call']['call_status'] = 'in-progress'
        
        response = self.app.post(
            '/call_events_manager',
            data=json.dumps(call_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Call not ended yet')
    
    @patch('server.app.ZendeskAPI')
    def test_create_zendesk_ticket_success(self, mock_zendesk_class):
        """Test successful manual ticket creation."""
        # Mock Zendesk API
        mock_zendesk_instance = Mock()
        mock_zendesk_class.return_value = mock_zendesk_instance
        mock_zendesk_instance.create_ticket.return_value = {
            "ticket": {
                "id": 12345,
                "subject": "Test Ticket",
                "status": "open",
                "requester_id": 67890,
                "tags": ["test", "voice-call"]
            }
        }
        
        response = self.app.post(
            '/create_zendesk_ticket',
            data=json.dumps(self.sample_ticket_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('ticket', data)
        self.assertEqual(data['ticket']['id'], 12345)
    
    def test_create_zendesk_ticket_missing_fields(self):
        """Test manual ticket creation with missing fields."""
        incomplete_data = {
            "subject": "Test Ticket"
            # Missing description and requester_phone
        }
        
        response = self.app.post(
            '/create_zendesk_ticket',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)
    
    @patch('server.app.ZendeskAPI')
    def test_create_zendesk_ticket_failure(self, mock_zendesk_class):
        """Test manual ticket creation failure."""
        # Mock Zendesk API to return None (failure)
        mock_zendesk_instance = Mock()
        mock_zendesk_class.return_value = mock_zendesk_instance
        mock_zendesk_instance.create_ticket.return_value = None
        
        response = self.app.post(
            '/create_zendesk_ticket',
            data=json.dumps(self.sample_ticket_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', data)
    
    @patch('server.app.ZendeskAPI')
    def test_test_zendesk_flow_success(self, mock_zendesk_class):
        """Test successful Zendesk flow test."""
        # Mock Zendesk API
        mock_zendesk_instance = Mock()
        mock_zendesk_class.return_value = mock_zendesk_instance
        
        # Mock user search
        mock_zendesk_instance.search_user_by_phone.return_value = [
            {"id": 67890, "name": "John Doe"}
        ]
        
        # Mock ticket creation
        mock_zendesk_instance.create_ticket.return_value = {
            "ticket": {
                "id": 12345,
                "subject": "Test Ticket",
                "status": "open"
            }
        }
        
        # Mock ticket update
        mock_zendesk_instance.update_ticket.return_value = {
            "ticket": {
                "id": 12345,
                "status": "solved"
            }
        }
        
        response = self.app.get('/test_zendesk_flow')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('test_results', data)
        self.assertTrue(data['test_results']['ticket_created'])
        self.assertTrue(data['test_results']['ticket_updated'])
    
    @patch('server.app.ZendeskAPI')
    def test_test_zendesk_flow_failure(self, mock_zendesk_class):
        """Test Zendesk flow test failure."""
        # Mock Zendesk API to return None for ticket creation
        mock_zendesk_instance = Mock()
        mock_zendesk_class.return_value = mock_zendesk_instance
        mock_zendesk_instance.search_user_by_phone.return_value = []
        mock_zendesk_instance.create_ticket.return_value = None
        
        response = self.app.get('/test_zendesk_flow')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 500)
        self.assertFalse(data['success'])
        self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main() 