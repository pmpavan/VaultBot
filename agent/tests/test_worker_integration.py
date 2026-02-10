"""
Integration tests for Classifier Worker
Story: 1.3 - Payload Parser & Classification

These tests verify the end-to-end functionality of the worker
with mocked database and Twilio interactions.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from worker import ClassifierWorker


class TestClassifierWorkerIntegration(unittest.TestCase):
    """Integration tests for ClassifierWorker."""
    
    def setUp(self):
        """Set up test environment."""
        # Set required environment variables
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
        os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-key'
        os.environ['TWILIO_ACCOUNT_SID'] = 'test-sid'
        os.environ['TWILIO_AUTH_TOKEN'] = 'test-token'
        os.environ['TWILIO_PHONE_NUMBER'] = '+1234567890'
    
    @patch('worker.get_messaging_provider')
    @patch('worker.create_client')
    def test_worker_initialization_success(self, mock_supabase, mock_messaging_factory):
        """Test worker initializes successfully with valid env vars."""
        worker = ClassifierWorker()
        
        self.assertIsNotNone(worker.supabase)
        self.assertIsNotNone(worker.messaging)
        mock_supabase.assert_called_once()
        mock_messaging_factory.assert_called_once()
    
    @patch('worker.get_messaging_provider')
    @patch('worker.create_client')
    def test_worker_initialization_missing_env_vars(self, mock_supabase, mock_messaging_factory):
        """Test worker raises error when env vars are missing."""
        del os.environ['SUPABASE_URL']
        
        with self.assertRaises(EnvironmentError) as context:
            ClassifierWorker()
        
        self.assertIn('SUPABASE_URL', str(context.exception))
        
        # Restore env var
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
    
    @patch('worker.get_messaging_provider')
    @patch('worker.create_client')
    def test_fetch_and_lock_job_success(self, mock_supabase, mock_messaging_factory):
        """Test fetching and locking a job successfully."""
        # Setup mock
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        
        mock_result = Mock()
        mock_result.data = [{'id': 'job-123', 'payload': {'Body': 'test'}}]
        mock_client.rpc.return_value.execute.return_value = mock_result
        
        # Test
        worker = ClassifierWorker()
        job = worker.fetch_and_lock_job()
        
        self.assertIsNotNone(job)
        self.assertEqual(job['id'], 'job-123')
        mock_client.rpc.assert_called_with('claim_pending_job', {})
    
    @patch('worker.get_messaging_provider')
    @patch('worker.create_client')
    def test_fetch_and_lock_job_empty_queue(self, mock_supabase, mock_messaging_factory):
        """Test fetching job when queue is empty."""
        # Setup mock
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        
        mock_result = Mock()
        mock_result.data = []
        mock_client.rpc.return_value.execute.return_value = mock_result
        
        # Test
        worker = ClassifierWorker()
        job = worker.fetch_and_lock_job()
        
        self.assertIsNone(job)
    
    @patch('worker.get_messaging_provider')
    @patch('worker.create_client')
    def test_classify_and_update_success(self, mock_supabase, mock_messaging_factory):
        """Test successful job classification and database update."""
        # Setup mocks
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        
        job = {
            'id': 'job-123',
            'payload': {
                'NumMedia': '0',
                'Body': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            }
        }
        
        # Test
        worker = ClassifierWorker()
        result = worker.classify_and_update(job)
        
        self.assertTrue(result)
        
        # Verify database update was called
        mock_client.table.assert_called_with('jobs')
        update_call = mock_client.table.return_value.update
        update_call.assert_called_once()
        
        # Verify update data
        update_data = update_call.call_args[0][0]
        self.assertEqual(update_data['content_type'], 'link')
        self.assertEqual(update_data['platform'], 'youtube')
        self.assertEqual(update_data['status'], 'pending')
    
    
    @patch('worker.get_messaging_provider')
    @patch('worker.create_client')
    def test_process_one_job_end_to_end(self, mock_supabase, mock_messaging_factory):
        """Test complete job processing flow."""
        # Setup mocks
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        
        # Mock fetch job
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{
            'id': 'job-123',
            'payload': {
                'NumMedia': '1',
                'MediaContentType0': 'image/jpeg',
                'Body': ''
            }
        }]
        mock_client.rpc.return_value.execute.return_value = mock_rpc_result
        
        # Test
        worker = ClassifierWorker()
        result = worker.process_one_job()
        
        self.assertTrue(result)
        
        # Verify job was fetched
        mock_client.rpc.assert_called_with('claim_pending_job', {})
        
        # Verify job was updated with classification
        update_call = mock_client.table.return_value.update
        update_data = update_call.call_args[0][0]
        self.assertEqual(update_data['content_type'], 'image')
        self.assertIsNone(update_data['platform'])


if __name__ == '__main__':
    unittest.main()
