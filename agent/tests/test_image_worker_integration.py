import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from image_worker import ImageWorker

class TestImageWorkerIntegration(unittest.TestCase):
    """Integration tests for ImageWorker."""
    
    def setUp(self):
        """Set up test environment."""
        # Set required environment variables
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
        os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-key'
        os.environ['TWILIO_ACCOUNT_SID'] = 'test-sid'
        os.environ['TWILIO_AUTH_TOKEN'] = 'test-token'
        os.environ['TWILIO_PHONE_NUMBER'] = '+1234567890'
    
    @patch('image_worker.get_messaging_provider')
    @patch('image_worker.create_client')
    def test_worker_initialization_success(self, mock_supabase, mock_messaging_factory):
        """Test worker initializes successfully with valid env vars."""
        worker = ImageWorker()
        
        self.assertIsNotNone(worker.supabase)
        self.assertIsNotNone(worker.messaging)
        mock_supabase.assert_called_once()
        mock_messaging_factory.assert_called_once()
    
    @patch('image_worker.get_messaging_provider')
    @patch('image_worker.create_client')
    def test_worker_initialization_missing_env_vars(self, mock_supabase, mock_messaging_factory):
        """Test worker raises error when env vars are missing."""
        del os.environ['SUPABASE_URL']
        
        with self.assertRaises(EnvironmentError) as context:
            ImageWorker()
        
        self.assertIn('SUPABASE_URL', str(context.exception))
        
        # Restore env var
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
    
    @patch('image_worker.get_messaging_provider')
    @patch('image_worker.create_client')
    @patch('nodes.image_processor.create_image_processor_graph')
    @patch('image_worker.NormalizerService')
    @patch('image_worker.SummarizerService')
    def test_process_and_update_with_twilio_media(self, mock_summarizer, mock_normalizer, mock_graph, mock_supabase, mock_messaging):
        """Test processing a job with single Twilio media URL."""
        # Setup mocks
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        
        # Setup successful image processing response
        mock_graph_instance.invoke.return_value = {
            'job_id': 'job-123',
            'url': 'https://api.twilio.com/media/123',
            'image_summary': 'An image of a fast food receipt.',
            'metadata': {'platform': 'twilio'},
            'error': None
        }
        
        # Setup DB selects/inserts
        # link_metadata select (simulate existing link not found)
        mock_existing = Mock()
        mock_existing.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_existing
        
        # link_metadata insert
        mock_insert = Mock()
        mock_insert.data = [{'id': 'link-123'}]
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_insert
        
        # Initialize worker instances using mocked dependencies
        worker = ImageWorker()
        worker.image_processor = mock_graph_instance
        
        job = {
            'id': 'job-123',
            'payload': {
                'From': 'whatsapp:+1234567890',
                'MessageSid': 'msg-123',
                'MediaUrl0': 'https://api.twilio.com/media/123'
            }
        }
        
        # Test
        result = worker.process_and_update(job)
        
        self.assertTrue(result)
        
        # Verify job was updated with success
        mock_client.table.assert_any_call('jobs')
        update_call = mock_client.table.return_value.update
        update_data = update_call.call_args[0][0]
        self.assertEqual(update_data['status'], 'complete')
        self.assertIn('images', update_data['result'])
        self.assertEqual(len(update_data['result']['images']), 1)

    @patch('image_worker.get_messaging_provider')
    @patch('image_worker.create_client')
    @patch('nodes.image_processor.create_image_processor_graph')
    @patch('image_worker.NormalizerService')
    @patch('image_worker.SummarizerService')
    def test_process_and_update_with_multiple_twilio_media(self, mock_summarizer, mock_normalizer, mock_graph, mock_supabase, mock_messaging):
        """Test processing a job with multiple Twilio media URLs."""
        # Setup mocks
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        
        # Setup successful image processing response
        mock_graph_instance.invoke.return_value = {
            'image_summary': 'An image of something.',
            'metadata': {'platform': 'twilio'},
            'error': None
        }
        
        worker = ImageWorker()
        worker.image_processor = mock_graph_instance
        
        job = {
            'id': 'job-456',
            'payload': {
                'From': 'whatsapp:+1234567890',
                'MessageSid': 'msg-456',
                'MediaUrl0': 'https://api.twilio.com/media/img0',
                'MediaUrl1': 'https://api.twilio.com/media/img1',
                'MediaUrl2': 'https://api.twilio.com/media/img2'
            }
        }
        
        # Test
        result = worker.process_and_update(job)
        
        self.assertTrue(result)
        self.assertEqual(mock_graph_instance.invoke.call_count, 3)

if __name__ == '__main__':
    unittest.main()
