"""
Unit tests for Content Classifier
Story: 1.3 - Payload Parser & Classification
"""

import unittest
from nodes.classifier import ContentClassifier, classify_job_payload


class TestContentClassifier(unittest.TestCase):
    """Test cases for ContentClassifier."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.classifier = ContentClassifier()
    
    def test_detect_video_media(self):
        """Test video media detection from Twilio payload."""
        payload = {
            'NumMedia': '1',
            'MediaContentType0': 'video/mp4',
            'Body': ''
        }
        
        content_type, platform = self.classifier.detect_content_type(payload)
        
        self.assertEqual(content_type, 'video')
        self.assertIsNone(platform)
    
    def test_detect_image_media(self):
        """Test image media detection from Twilio payload."""
        payload = {
            'NumMedia': '1',
            'MediaContentType0': 'image/jpeg',
            'Body': ''
        }
        
        content_type, platform = self.classifier.detect_content_type(payload)
        
        self.assertEqual(content_type, 'image')
        self.assertIsNone(platform)
    
    def test_detect_youtube_link(self):
        """Test YouTube URL detection."""
        payload = {
            'NumMedia': '0',
            'Body': 'Check this out: https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        }
        
        content_type, platform = self.classifier.detect_content_type(payload)
        
        self.assertEqual(content_type, 'link')
        self.assertEqual(platform, 'youtube')
    
    def test_detect_youtube_short_link(self):
        """Test YouTube short URL detection."""
        payload = {
            'NumMedia': '0',
            'Body': 'https://youtu.be/dQw4w9WgXcQ'
        }
        
        content_type, platform = self.classifier.detect_content_type(payload)
        
        self.assertEqual(content_type, 'link')
        self.assertEqual(platform, 'youtube')
    
    def test_detect_instagram_link(self):
        """Test Instagram URL detection."""
        payload = {
            'NumMedia': '0',
            'Body': 'Amazing reel: https://www.instagram.com/reel/ABC123xyz/'
        }
        
        content_type, platform = self.classifier.detect_content_type(payload)
        
        self.assertEqual(content_type, 'link')
        self.assertEqual(platform, 'instagram')
    
    def test_detect_tiktok_link(self):
        """Test TikTok URL detection."""
        payload = {
            'NumMedia': '0',
            'Body': 'https://www.tiktok.com/@user/video/1234567890'
        }
        
        content_type, platform = self.classifier.detect_content_type(payload)
        
        self.assertEqual(content_type, 'link')
        self.assertEqual(platform, 'tiktok')
    
    def test_detect_udemy_link(self):
        """Test Udemy URL detection."""
        payload = {
            'NumMedia': '0',
            'Body': 'Great course: https://www.udemy.com/course/python-bootcamp/'
        }
        
        content_type, platform = self.classifier.detect_content_type(payload)
        
        self.assertEqual(content_type, 'link')
        self.assertEqual(platform, 'udemy')
    
    def test_detect_coursera_link(self):
        """Test Coursera URL detection."""
        payload = {
            'NumMedia': '0',
            'Body': 'Check out: https://www.coursera.org/learn/machine-learning'
        }
        
        content_type, platform = self.classifier.detect_content_type(payload)
        
        self.assertEqual(content_type, 'link')
        self.assertEqual(platform, 'coursera')
    
    def test_detect_generic_link(self):
        """Test generic URL detection."""
        payload = {
            'NumMedia': '0',
            'Body': 'Visit https://example.com for more info'
        }
        
        content_type, platform = self.classifier.detect_content_type(payload)
        
        self.assertEqual(content_type, 'link')
        self.assertEqual(platform, 'generic')
    
    def test_detect_plain_text(self):
        """Test plain text message detection."""
        payload = {
            'NumMedia': '0',
            'Body': 'Just a regular text message'
        }
        
        content_type, platform = self.classifier.detect_content_type(payload)
        
        self.assertEqual(content_type, 'text')
        self.assertIsNone(platform)
    
    def test_classify_job_payload_function(self):
        """Test the classify_job_payload wrapper function."""
        payload = {
            'NumMedia': '0',
            'Body': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        }
        
        result = classify_job_payload(payload)
        
        self.assertEqual(result['content_type'], 'link')
        self.assertEqual(result['platform'], 'youtube')


if __name__ == '__main__':
    unittest.main()
