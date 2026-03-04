#!/usr/bin/env python3
"""
OpenClaw API Connectivity Test
验证 OPENCLAW_API_KEY 是否正确配置并可用
"""

import os
import sys

def test_env_var():
    """Test 1: 环境变量是否存在"""
    print("=" * 60)
    print("Test 1: Environment Variable Check")
    print("=" * 60)
    
    api_key = os.getenv("OPENCLAW_API_KEY")
    if api_key:
        print(f"[OK] OPENCLAW_API_KEY is set")
        print(f"     Length: {len(api_key)} chars")
        print(f"     Prefix: {api_key[:10]}...")
        return True
    else:
        print("[FAIL] OPENCLAW_API_KEY is NOT set")
        return False

def test_anthropic_connection():
    """Test 2: Anthropic API 连通性"""
    print("\n" + "=" * 60)
    print("Test 2: Anthropic API Connection Test")
    print("=" * 60)
    
    try:
        import anthropic
        
        api_key = os.getenv("OPENCLAW_API_KEY")
        base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        
        print(f"Base URL: {base_url}")
        print(f"Model: claude-opus-4-6")
        print("\nSending test message...")
        
        client = anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url
        )
        
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Reply with exactly: PING_OK"}
            ]
        )
        
        response = message.content[0].text.strip()
        print(f"\nResponse: {response}")
        
        if "PING_OK" in response:
            print("\n[OK] API connection successful!")
            print(f"     Usage: {message.usage.input_tokens} in, {message.usage.output_tokens} out")
            return True
        else:
            print(f"\n[WARN] Unexpected response: {response}")
            return False
            
    except ImportError:
        print("[SKIP] anthropic package not installed")
        print("      Install with: pip install anthropic")
        return None
    except Exception as e:
        print(f"\n[FAIL] API connection failed: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("OpenClaw API Connectivity Test")
    print("=" * 60)
    print()
    
    results = {
        "Environment Variable": test_env_var(),
        "API Connection": test_anthropic_connection()
    }
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is True:
            status = "[OK]"
        elif result is False:
            status = "[FAIL]"
        else:
            status = "[SKIP]"
        print(f"{status} {test_name}")
    
    if all(r is True for r in results.values() if r is not None):
        print("\n[SUCCESS] All tests passed!")
        print("OpenClaw is ready for production.")
        return 0
    else:
        print("\n[WARNING] Some tests failed or were skipped.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
