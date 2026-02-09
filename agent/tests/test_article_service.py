import unittest
from unittest.mock import MagicMock, patch
from agent.src.tools.article.service import ArticleService
from agent.src.tools.article.types import ArticleExtractionRequest, ArticleExtractionResponse

class TestArticleService(unittest.TestCase):
    
    def setUp(self):
        self.service = ArticleService()
        
    def test_extract_primary_success(self):
        # Mock primary extractor
        self.service.trafilatura.extract = MagicMock(return_value=ArticleExtractionResponse(
            text="Primary content", 
            url="http://test.com"
        ))
        
        request = ArticleExtractionRequest(url="http://test.com")
        response = self.service.extract(request)
        
        self.assertEqual(response.text, "Primary content")
        self.service.trafilatura.extract.assert_called_once()
        
    def test_extract_fallback(self):
        # Mock primary failure
        self.service.trafilatura.extract = MagicMock(side_effect=Exception("Primary failed"))
        
        # Mock fallback success
        self.service.newspaper.extract = MagicMock(return_value=ArticleExtractionResponse(
            text="Fallback content", 
            url="http://test.com"
        ))
        
        request = ArticleExtractionRequest(url="http://test.com")
        response = self.service.extract(request)
        
        self.assertEqual(response.text, "Fallback content")
        self.service.newspaper.extract.assert_called_once()

if __name__ == '__main__':
    unittest.main()
