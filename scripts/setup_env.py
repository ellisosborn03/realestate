#!/usr/bin/env python3
"""
Environment Setup for Real Estate Tool
Run this script to create your .env file with API keys
"""

import os

def create_env_file():
    """Create .env file with API key template"""
    
    env_content = """# Real Estate API Keys Configuration
# Add your actual API keys below

# Google Maps/Places API Key
# Get from: https://console.cloud.google.com/
# Enable: Places API, Maps JavaScript API
GOOGLE_API_KEY=your_google_api_key_here

# ATTOM Data API Key (already working)
ATTOM_API_KEY=ad91f2f30426f1ee54aec35791aaa044

# OpenAI API Key (for GPT address fixing)
# Get from: https://platform.openai.com/api-keys  
OPENAI_API_KEY=your_openai_api_key_here
"""

    # Check if .env already exists
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cancelled. Existing .env file preserved.")
            return
    
    # Write the .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Created .env file successfully!")
        print("\n📝 Next steps:")
        print("1. Edit .env file and replace 'your_google_api_key_here' with your actual Google API key")
        print("2. Get Google API key from: https://console.cloud.google.com/")
        print("3. Enable Places API in Google Cloud Console")
        print("4. Run: python3 complete_address_test.py")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

def show_current_env():
    """Show current environment variables"""
    print("\n🔍 Current Environment Variables:")
    
    if os.path.exists('.env'):
        print("📁 .env file exists")
        with open('.env', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    key = line.split('=')[0]
                    value = line.split('=')[1].strip() if '=' in line else ''
                    if 'your_' in value:
                        print(f"  ❌ {key}: Not set")
                    else:
                        print(f"  ✅ {key}: Configured")
    else:
        print("📁 No .env file found")
    
    # Check environment
    google_key = os.getenv('GOOGLE_API_KEY')
    attom_key = os.getenv('ATTOM_API_KEY')
    
    print(f"\n🌍 System Environment:")
    print(f"  GOOGLE_API_KEY: {'✅ Set' if google_key else '❌ Not set'}")
    print(f"  ATTOM_API_KEY: {'✅ Set' if attom_key else '❌ Not set'}")

def main():
    print("🏠 Real Estate Tool - Environment Setup")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Create/update .env file")
        print("2. Show current environment status")
        print("3. Test API keys")
        print("4. Exit")
        
        choice = input("\nChoose option (1-4): ").strip()
        
        if choice == '1':
            create_env_file()
        elif choice == '2':
            show_current_env()
        elif choice == '3':
            test_api_keys()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")

def test_api_keys():
    """Test if API keys are working"""
    print("\n🧪 Testing API Keys...")
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    google_key = os.getenv('GOOGLE_API_KEY')
    attom_key = os.getenv('ATTOM_API_KEY')
    
    # Test Google API
    if google_key and google_key != 'your_google_api_key_here':
        try:
            import requests
            url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
            params = {
                "input": "1600 Amphitheatre Parkway, Mountain View, CA",
                "key": google_key
            }
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            
            if data.get("status") == "OK":
                print("  ✅ Google Places API: Working")
            else:
                print(f"  ❌ Google Places API: Error - {data.get('status')}")
        except Exception as e:
            print(f"  ❌ Google Places API: Error - {e}")
    else:
        print("  ⏭️  Google Places API: Not configured")
    
    # Test ATTOM API
    if attom_key:
        try:
            import requests
            url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/attomavm/detail"
            params = {"address1": "920 POPLAR DRIVE", "address2": "LAKE PARK, FL 33403"}
            headers = {"accept": "application/json", "apikey": attom_key}
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            
            if resp.status_code == 200:
                print("  ✅ ATTOM API: Working")
            else:
                print(f"  ❌ ATTOM API: Error - {resp.status_code}")
        except Exception as e:
            print(f"  ❌ ATTOM API: Error - {e}")
    else:
        print("  ❌ ATTOM API: Not configured")

if __name__ == "__main__":
    main() 