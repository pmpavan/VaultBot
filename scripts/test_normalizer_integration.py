import os
import sys
import unittest
import json
from unittest.mock import MagicMock, patch

# Add project root and agent/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../agent/src'))

from agent.src.scraper_worker import ScraperWorker
from agent.src.tools.normalizer.types import NormalizerResponse, CategoryEnum, PriceRangeEnum

class TestNormalizerIntegration(unittest.TestCase):
    
    @patch.dict(os.environ, {'SUPABASE_URL': 'http://test', 'SUPABASE_SERVICE_ROLE_KEY': 'test'})
    @patch('agent.src.scraper_worker.ScraperService')
    @patch('agent.src.scraper_worker.get_messaging_provider')
    @patch('agent.src.scraper_worker.create_client')
    def test_scraper_worker_integration(self, mock_supabase, mock_messaging, mock_scraper_service):
        
        # Setup Scraper Worker
        worker = ScraperWorker()
        
        # Mock Normalizer Service
        mock_normalizer = MagicMock()
        worker.normalizer_service = mock_normalizer
        
        # Mock Normalizer Response
        mock_norm_response = NormalizerResponse(
            category=CategoryEnum.FOOD,
            price_range=PriceRangeEnum.MODERATE,
            tags=['Sushi', 'Tokyo', 'Food']
        )
        mock_normalizer.normalize.return_value = mock_norm_response
        
        # Mock Job
        job = {
            'id': 'job-123',
            'payload': {
                'Body': 'http://example.com/sushi',
                'From': 'whatsapp:+1234567890'
            },
            'source_channel_id': 'whatsapp:+1234567890',
            'source_type': 'dm'
        }
        
        # Mock Scraper Service
        mock_metadata = MagicMock()
        mock_metadata.title = "Sushi Place"
        mock_metadata.description = "Best sushi in Tokyo"
        mock_metadata.platform = "generic"
        mock_metadata.content_type = "link"
        mock_metadata.extraction_strategy = "opengraph"
        mock_metadata.author = None
        mock_metadata.thumbnail_url = None
        
        worker.scraper_service.scrape.return_value = mock_metadata
        
        # Mock Supabase
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        
        # Mock link_metadata lookup (existing)
        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [{'id': 'link-123', 'scrape_count': 1}]
        
        # Run process_and_update
        worker.process_and_update(job)
        
        # Verify Normalizer was called
        mock_normalizer.normalize.assert_called_once()
        
        # Verify Supabase Update included normalized fields
        # Check all calls to table('link_metadata').update(...)
        calls = mock_client.table.return_value.update.call_args_list
        
        normalized_update_found = False
        for call in calls:
            args, _ = call
            data = args[0]
            if 'normalized_category' in data:
                print(f"DEBUG: Found update with normalized data: {data}")
                if data['normalized_category'] == 'Food' and \
                   data['normalized_price_range'] == '$$' and \
                   data['normalized_tags'] == ['Sushi', 'Tokyo', 'Food']:
                    normalized_update_found = True
                    break
        
        self.assertTrue(normalized_update_found, "Normalized data not passed to Supabase update")

import logging
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    unittest.main()
