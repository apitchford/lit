#!/usr/bin/env python3
"""
Test script to validate Kindle Article Sender installation
"""
import sys
import os

def test_imports():
    """Test that all required packages can be imported"""
    print("Testing imports...")
    try:
        import flask
        print("✓ Flask")
        import trafilatura
        print("✓ trafilatura")
        import ebooklib
        print("✓ ebooklib")
        from PIL import Image
        print("✓ Pillow")
        import requests
        print("✓ requests")
        import bs4
        print("✓ BeautifulSoup4")
        print("\nAll required packages imported successfully!")
        return True
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def test_playwright():
    """Test Playwright installation"""
    print("\nTesting Playwright...")
    try:
        from playwright.sync_api import sync_playwright
        print("✓ Playwright imported")
        
        # Try to launch browser
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        print("✓ Chromium browser working")
        return True
    except Exception as e:
        print(f"⚠️  Playwright issue: {e}")
        print("Run: playwright install chromium")
        return False

def test_env():
    """Test .env configuration"""
    print("\nTesting .env configuration...")
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'SMTP_SERVER',
        'SMTP_PORT', 
        'SMTP_USERNAME',
        'SMTP_PASSWORD',
        'FROM_EMAIL',
        'KINDLE_EMAIL'
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f"your-{var.lower().replace('_', '-')}":
            print(f"✓ {var}")
        else:
            print(f"⚠️  {var} not configured")
            missing.append(var)
    
    if missing:
        print(f"\n⚠️  Please configure these variables in .env file:")
        for var in missing:
            print(f"   - {var}")
        return False
    
    print("\n✓ All environment variables configured")
    return True

def test_modules():
    """Test custom modules"""
    print("\nTesting custom modules...")
    try:
        from extractor import ArticleExtractor
        print("✓ ArticleExtractor")
        from image_processor import ImageProcessor
        print("✓ ImageProcessor")
        from epub_generator import EPUBGenerator
        print("✓ EPUBGenerator")
        from mailer import KindleMailer
        print("✓ KindleMailer")
        print("\n✓ All custom modules loaded successfully")
        return True
    except Exception as e:
        print(f"\n❌ Module error: {e}")
        return False

def main():
    print("=" * 60)
    print("  Kindle Article Sender - Installation Test")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Playwright", test_playwright()))
    results.append(("Environment", test_env()))
    results.append(("Custom Modules", test_modules()))
    
    print("\n" + "=" * 60)
    print("  Test Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:20} {status}")
    
    all_passed = all(r[1] for r in results)
    
    print()
    if all_passed:
        print("🎉 All tests passed! You're ready to run the application.")
        print("\nRun: python app.py")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nFor help, see README.md")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
