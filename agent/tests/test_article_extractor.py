import unittest
from unittest.mock import MagicMock, patch
from agent.src.tools.article.extractors.trafilatura_extractor import TrafilaturaExtractor
from agent.src.tools.article.extractors.newspaper_extractor import NewspaperExtractor
from agent.src.tools.article.types import ArticleExtractionError

class TestTrafilaturaExtractor(unittest.TestCase):
    
    def setUp(self):
        self.extractor = TrafilaturaExtractor()
        
    @patch('trafilatura.extract')
    @patch('requests.get')
    def test_extract_success(self, mock_get, mock_extract):
        # Mock requests
        mock_response = MagicMock()
        mock_response.text = '<html><body><p>Test content</p></body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Mock trafilatura
        mock_extract.return_value = "Test content"
        
        response = self.extractor.extract("https://example.com")
        
        self.assertEqual(response.text, "Test content")
        self.assertEqual(response.url, "https://example.com")
        
    @patch('trafilatura.extract')
    @patch('requests.get')
    def test_extract_failure(self, mock_get, mock_extract):
        # Mock requests failure
        mock_get.side_effect = Exception("Network error")
        
        with self.assertRaises(Exception): # The extractor re-raises as ProxyError or ArticleExtractionError
            self.extractor.extract("https://example.com")

class TestNewspaperExtractor(unittest.TestCase):
    
    def setUp(self):
        self.extractor = NewspaperExtractor()
        
    @patch('newspaper.Article')
    def test_extract_success(self, mock_article_class):
        # Mock newspaper Article
        mock_article = MagicMock()
        mock_article.text = "Newspaper extracted content"
        mock_article.title = "Test Article"
        mock_article.authors = ["John Doe"]
        mock_article.publish_date = None
        mock_article_class.return_value = mock_article
        
        response = self.extractor.extract("https://example.com/news")
        
        self.assertEqual(response.text, "Newspaper extracted content")
        self.assertEqual(response.title, "Test Article")
        self.assertEqual(response.author, "John Doe")
        
    @patch('newspaper.Article')
    def test_extract_failure(self, mock_article_class):
        # Mock newspaper failure
        mock_article = MagicMock()
        mock_article.download.side_effect = Exception("Download failed")
        mock_article_class.return_value = mock_article
        
        with self.assertRaises(Exception):
            self.extractor.extract("https://example.com/news")

if __name__ == '__main__':
    unittest.main()

