import unittest
from agent.src.tools.article.classifier import ContentClassifier

class TestContentClassifier(unittest.TestCase):
    
    def setUp(self):
        self.classifier = ContentClassifier()
        
    def test_documentation(self):
        self.assertEqual(self.classifier.classify('https://docs.python.org/3/library/os.html'), 'documentation')
        self.assertEqual(self.classifier.classify('https://readthedocs.io/en/stable/'), 'documentation')
        self.assertEqual(self.classifier.classify('https://example.com/docs/api'), 'documentation')
        
    def test_blog(self):
        self.assertEqual(self.classifier.classify('https://simonwillison.net/2024/Feb/5/blog-post'), 'blog')
        self.assertEqual(self.classifier.classify('https://medium.com/@user/story'), 'blog')
        self.assertEqual(self.classifier.classify('https://company.com/blog/update'), 'blog')
        
    def test_article(self):
        self.assertEqual(self.classifier.classify('https://www.nytimes.com/2024/02/09/world/news.html'), 'article')
        self.assertEqual(self.classifier.classify('https://www.bbc.com/news/technology-12345'), 'article')
        
    def test_generic(self):
        self.assertEqual(self.classifier.classify('https://google.com'), 'generic')
        self.assertEqual(self.classifier.classify('https://example.com/page'), 'generic')

if __name__ == '__main__':
    unittest.main()
