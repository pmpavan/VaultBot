#!/usr/bin/env python3
"""
Live Integration Test for Vision Service
Tests real API calls to OpenRouter (GPT-4o and Gemini)
"""
import sys
import os
import argparse
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.src.tools.vision import VisionService, VisionRequest

def test_openai_vision(image_url: str, prompt: str):
    """Test Vision Service with OpenAI GPT-4o via OpenRouter"""
    print("\n🔍 Testing OpenAI GPT-4o via OpenRouter...")
    
    service = VisionService()
    request = VisionRequest(
        image_input=image_url,
        prompt=prompt,
        model_provider="openai"
    )
    
    try:
        response = service.analyze(request)
        print(f"✅ Success!")
        print(f"Provider: {response.provider_used}")
        print(f"Analysis Data: {json.dumps(response.analysis_data, indent=2)}")
        if response.usage_metadata:
            print(f"Tokens Used: {response.usage_metadata.get('total_tokens', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False

def test_gemini_vision(image_url: str, prompt: str):
    """Test Vision Service with Gemini 1.5 Pro via OpenRouter"""
    print("\n🔍 Testing Gemini 1.5 Pro via OpenRouter...")
    
    service = VisionService()
    request = VisionRequest(
        image_input=image_url,
        prompt=prompt,
        model_provider="gemini"
    )
    
    try:
        response = service.analyze(request)
        print(f"✅ Success!")
        print(f"Provider: {response.provider_used}")
        print(f"Analysis Data: {json.dumps(response.analysis_data, indent=2)}")
        if response.usage_metadata:
            print(f"Tokens Used: {response.usage_metadata.get('total_tokens', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Live test for Vision Service")
    parser.add_argument(
        "--image", 
        default="https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
        help="Image URL to analyze"
    )
    parser.add_argument(
        "--prompt",
        default="Describe this image in detail",
        help="Analysis prompt"
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "gemini", "both"],
        default="both",
        help="Which provider to test"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        sys.exit(1)
    
    print("=" * 60)
    print("Vision Service Live Integration Test")
    print("=" * 60)
    print(f"Image: {args.image}")
    print(f"Prompt: {args.prompt}")
    
    results = []
    
    if args.provider in ["openai", "both"]:
        results.append(test_openai_vision(args.image, args.prompt))
    
    if args.provider in ["gemini", "both"]:
        results.append(test_gemini_vision(args.image, args.prompt))
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
