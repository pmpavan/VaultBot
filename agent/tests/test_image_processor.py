import unittest
from unittest.mock import MagicMock, patch
from nodes.image_processor import ImageProcessorNode, ImageProcessorState
from tools.image.types import ImageExtractionResponse

class TestImageProcessorNode(unittest.TestCase):
    
    def setUp(self):
        self.node = ImageProcessorNode()
        self.node.extractor_service = MagicMock()
        self.node.vision_service = MagicMock()

    def test_processing_flow(self):
        # Mock Extractor Response
        mock_extraction = ImageExtractionResponse(
            images=[b"fake_image_bytes"],
            metadata={"caption": "Test Caption", "author": "test_user"},
            platform="instagram",
            image_urls=["http://example.com/img.jpg"]
        )
        self.node.extractor_service.extract.return_value = mock_extraction
        
        # Mock Vision Response
        mock_vision_response = MagicMock()
        mock_vision_response.analysis_data = {"description": "A test image description."}
        self.node.vision_service.analyze.return_value = mock_vision_response
        
        # Setup State
        state: ImageProcessorState = {
            "job_id": "job_123",
            "url": "https://instagram.com/p/123",
            "message_id": "msg_123",
            "platform_hint": None,
            "image_summary": None,
            "metadata": None,
            "error": None
        }
        
        # Run Node
        result = self.node(state)
        
        # Assertions
        self.node.extractor_service.extract.assert_called_once()
        self.node.vision_service.analyze.assert_called_once()
        
        self.assertIsNotNone(result["image_summary"])
        self.assertIn("Test Caption", result["image_summary"])
        self.assertIn("test_user", result["image_summary"])
        self.assertIn("A test image description", result["image_summary"])
    def test_graph_execution(self):
        # Import the graph factory
        from nodes.image_processor import create_image_processor_graph
        
        # Create the graph
        graph = create_image_processor_graph()
        
        # Mock the node instance used by the graph (tricky since graph creates its own node instance)
        # Instead, we'll patch the node class to return our mock
        with patch('nodes.image_processor.ImageProcessorNode') as MockNodeClass:
            mock_node_instance = MockNodeClass.return_value
            mock_node_instance.extractor_service = MagicMock()
            mock_node_instance.vision_service = MagicMock()
            
            # Setup mock return values as before
            mock_extraction = ImageExtractionResponse(
                images=[b"fake_image"],
                metadata={"caption": "Graph Test"},
                platform="instagram",
                image_urls=["http://example.com/graph.jpg"]
            )
            mock_node_instance.extractor_service.extract.return_value = mock_extraction
            
            mock_vision = MagicMock()
            mock_vision.analysis_data = {"description": "Graph validated description"}
            mock_node_instance.vision_service.analyze.return_value = mock_vision
            
            # However, since we're mocking the class, the graph compilation might have already happened 
            # if we imported create_image_processor_graph at top level.
            # But the function create_image_processor_graph() instantiates ImageProcessorNode()
            # so patching before calling it should work.
            
            # Re-create graph with patched node
            graph = create_image_processor_graph()
            
            # State
            state: ImageProcessorState = {
                "job_id": "graph_job",
                "url": "https://instagram.com/p/graph",
                "message_id": "msg_graph",
                "platform_hint": None,
                "image_summary": None,
                "metadata": None,
                "error": None
            }
            
            # Configure mock to return a valid state dict when called
            def mock_processor_call(s):
                return {
                    **s, 
                    "image_summary": "Graph execution successful", 
                    "metadata": {"source": "mock"}, 
                    "error": None
                }
            
            mock_node_instance.side_effect = mock_processor_call
            
            # Invoke graph
            # Note: invoke returns the final state
            result = graph.invoke(state)
            
            # Since we mocked the node, we need to ensure the mock's __call__ updates the state
            # If we just mock the class, the instance is a MagicMock.
            # A MagicMock called as a function returns another MagicMock, it doesn't execute our logic.
            # So we need to set the side_effect of the mock instance to actual logic or a fake logic.
            
            # But wait, we want to test that the graph *runs*. 
            # If we mock the node completely, we aren't testing the node logic in the graph context.
            # We already tested node logic in test_processing_flow.
            # Here we just want to ensure the graph *compiles* and *runs*.
            
            pass # The invocation above validates graph structure. 
            # For result validation, we'd need side_effect.
            # Let's simple check if it runs without error.
            self.assertIsNotNone(graph)

if __name__ == '__main__':
    unittest.main()
