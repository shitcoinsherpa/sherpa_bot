#!/usr/bin/env python3
"""
OpenRouter Integration Installer
This script automatically applies OpenRouter integration to sherpa_bot.py
"""

import os
import shutil
from datetime import datetime

def create_backup():
    """Create a backup of the original file"""
    if os.path.exists('sherpa_bot.py'):
        backup_name = f"sherpa_bot_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        shutil.copy2('sherpa_bot.py', backup_name)
        print(f"✅ Created backup: {backup_name}")
        return True
    else:
        print("❌ sherpa_bot.py not found!")
        return False

def apply_openrouter_integration():
    """Apply OpenRouter integration to sherpa_bot.py"""
    
    print("\n🚀 OpenRouter Integration Installer")
    print("=" * 50)
    
    # Create backup
    if not create_backup():
        return False
    
    # Read the original file
    with open('sherpa_bot.py', 'r') as f:
        content = f.read()
    
    # Check if already integrated
    if 'OPENROUTER_BASE_URL' in content:
        print("⚠️  OpenRouter integration already appears to be installed!")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    print("\n📝 Applying OpenRouter integration...")
    
    # MODIFICATION 1: Add constants after existing constants
    constants_to_add = '''
# OpenRouter Integration Constants
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODELS_FILE = "openrouter_models.json"

# Default OpenRouter models - users can add more
DEFAULT_OPENROUTER_MODELS = {
    "OpenRouter: Claude 3.5 Sonnet": {
        "name": "anthropic/claude-3.5-sonnet",
        "provider": "openrouter"
    },
    "OpenRouter: Claude 3 Opus": {
        "name": "anthropic/claude-3-opus",
        "provider": "openrouter"
    },
    "OpenRouter: GPT-4o": {
        "name": "openai/gpt-4o",
        "provider": "openrouter"
    },
    "OpenRouter: GPT-4 Turbo": {
        "name": "openai/gpt-4-turbo",
        "provider": "openrouter"
    },
    "OpenRouter: Llama 3.1 405B": {
        "name": "meta-llama/llama-3.1-405b-instruct",
        "provider": "openrouter"
    },
    "OpenRouter: Mixtral 8x22B": {
        "name": "mistralai/mixtral-8x22b-instruct",
        "provider": "openrouter"
    },
    "OpenRouter: Gemini Pro 1.5": {
        "name": "google/gemini-pro-1.5",
        "provider": "openrouter"
    }
}
'''
    
    # Find where to insert constants (after OPENAI_MODELS definition)
    models_end = content.find('}\n\n', content.find('OPENAI_MODELS = {'))
    if models_end != -1:
        models_end += 3  # Include the closing braces and newlines
        content = content[:models_end] + constants_to_add + content[models_end:]
        print("✅ Added OpenRouter constants")
    
    # MODIFICATION 2: Update TwitterBot __init__ method
    # Add new attributes in __init__
    init_additions = '''        self.openrouter_models = {}  # Store custom OpenRouter models
        self.api_provider = self.credentials.get('api_provider', 'openai')  # Default to OpenAI for backward compatibility
        self.openrouter_client = None
'''
    
    # Find the right place to add these (after self.feed_config = {})
    init_pos = content.find('self.feed_config = {}')
    if init_pos != -1:
        insert_pos = content.find('\n', init_pos) + 1
        content = content[:insert_pos] + init_additions + content[insert_pos:]
        print("✅ Updated __init__ attributes")
    
    # Add OpenRouter model loading
    load_models_line = '''        self.openrouter_models = self.load_openrouter_models()
        print(f"Loaded OpenRouter models: {json.dumps(self.openrouter_models, indent=2)}")
        
'''
    
    # Insert after loading feed_config
    feed_load_pos = content.find('self.feed_config = self.load_feed_config()')
    if feed_load_pos != -1:
        insert_pos = content.find('\n', feed_load_pos) + 1
        # Find the print statement after it
        next_print = content.find('print(f"Loaded feed configuration:', insert_pos)
        if next_print != -1:
            insert_pos = content.find('\n', next_print) + 1
        content = content[:insert_pos] + load_models_line + content[insert_pos:]
        print("✅ Added OpenRouter model loading")
    
    # Add OpenRouter client initialization
    openrouter_init = '''
        # Initialize OpenRouter client if credentials exist
        if self.credentials.get('openrouter_key'):
            self.openrouter_client = OpenAI(
                api_key=self.credentials['openrouter_key'],
                base_url=OPENROUTER_BASE_URL,
                http_client=httpx.Client(
                    base_url=OPENROUTER_BASE_URL,
                    follow_redirects=True,
                    timeout=60.0,
                    headers={
                        "HTTP-Referer": "https://github.com/shitcoinsherpa/sherpa_bot",
                        "X-Title": "Sherpa Bot"
                    }
                )
            )
            print("OpenRouter client initialized")
'''
    
    # Insert after OpenAI client initialization
    openai_init_pos = content.find('print("OpenAI client initialized")')
    if openai_init_pos != -1:
        insert_pos = content.find('\n', openai_init_pos) + 1
        content = content[:insert_pos] + openrouter_init + content[insert_pos:]
        print("✅ Added OpenRouter client initialization")
    
    # MODIFICATION 3: Add new methods to TwitterBot class
    new_methods = '''
    def load_openrouter_models(self):
        """Load custom OpenRouter models from file"""
        try:
            if os.path.exists(OPENROUTER_MODELS_FILE):
                with open(OPENROUTER_MODELS_FILE, 'r') as f:
                    models = json.load(f)
                    # Merge with default models
                    all_models = DEFAULT_OPENROUTER_MODELS.copy()
                    all_models.update(models)
                    return all_models
            return DEFAULT_OPENROUTER_MODELS.copy()
        except Exception as e:
            print(f"Error loading OpenRouter models: {e}")
            return DEFAULT_OPENROUTER_MODELS.copy()
    
    def save_openrouter_models(self, models):
        """Save custom OpenRouter models to file"""
        try:
            # Only save custom models (not defaults)
            custom_models = {k: v for k, v in models.items() 
                           if k not in DEFAULT_OPENROUTER_MODELS}
            with open(OPENROUTER_MODELS_FILE, 'w') as f:
                json.dump(custom_models, f, indent=2)
            self.openrouter_models = models
            return True
        except Exception as e:
            print(f"Error saving OpenRouter models: {e}")
            return False
    
    def get_available_models(self):
        """Get all available models based on configured providers"""
        models = {}
        
        # Add OpenAI models if OpenAI is configured
        if self.credentials.get('openai_key'):
            for key, value in OPENAI_MODELS.items():
                models[key] = {**value, "provider": "openai"}
        
        # Add OpenRouter models if OpenRouter is configured
        if self.credentials.get('openrouter_key'):
            for key, value in self.openrouter_models.items():
                models[key] = value
        
        return models
    
    def get_client_for_model(self, model_info):
        """Get the appropriate client based on model provider"""
        provider = model_info.get('provider', 'openai')
        
        if provider == 'openrouter':
            if not self.openrouter_client:
                raise Exception("OpenRouter client not initialized. Please add OpenRouter API key.")
            return self.openrouter_client
        else:
            if not self.client:
                raise Exception("OpenAI client not initialized. Please add OpenAI API key.")
            return self.client
'''
    
    # Find a good place to insert these methods (after load_characters method)
    load_chars_pos = content.find('def load_characters(self):')
    if load_chars_pos != -1:
        # Find the end of load_characters method
        next_def = content.find('\n    def ', load_chars_pos + 10)
        if next_def != -1:
            content = content[:next_def] + new_methods + content[next_def:]
            print("✅ Added new OpenRouter methods")
    
    # MODIFICATION 4: Update generate_tweet to use the appropriate client
    # This is more complex, we need to modify the existing generate_tweet method
    
    # Find generate_tweet method
    gen_tweet_pos = content.find('def generate_tweet(self, character_name, topic):')
    if gen_tweet_pos != -1:
        # Find where the OpenAI client is called
        client_call_pos = content.find('response = self.client.chat.completions.create(', gen_tweet_pos)
        if client_call_pos != -1:
            # Add model detection code before the API call
            model_detection = '''
            # Get the appropriate client and model
            model_name = character.get('model', 'gpt-3.5-turbo')
            
            # Determine which client to use based on the model
            available_models = self.get_available_models()
            model_info = None
            
            # Find the model info
            for key, value in available_models.items():
                if value['name'] == model_name:
                    model_info = value
                    break
            
            # If model not found in available models, assume it's OpenAI
            if not model_info:
                model_info = {'name': model_name, 'provider': 'openai'}
            
            # Get the appropriate client
            api_client = self.get_client_for_model(model_info)
            
'''
            # Insert before the response line
            content = content[:client_call_pos] + model_detection + '            '
            
            # Replace self.client with api_client
            content = content.replace('response = self.client.chat.completions.create(', 
                                    'response = api_client.chat.completions.create(', 1)
            
            # Also update the retry call if it exists
            content = content.replace('response = self.client.chat.completions.create(', 
                                    'response = api_client.chat.completions.create(', 1)
            
            print("✅ Updated generate_tweet method")
    
    # MODIFICATION 5: Update save_credentials to handle OpenRouter
    save_creds_pos = content.find('def save_credentials(self, credentials):')
    if save_creds_pos != -1:
        # Find where to add OpenRouter client initialization
        twitter_init = content.find('print("Twitter client initialized")', save_creds_pos)
        if twitter_init != -1:
            insert_pos = content.find('\n', twitter_init) + 1
            openrouter_save_init = '''
                # Initialize OpenRouter client if key provided
                if credentials.get('openrouter_key'):
                    print("Initializing OpenRouter client...")
                    self.openrouter_client = OpenAI(
                        api_key=credentials['openrouter_key'],
                        base_url=OPENROUTER_BASE_URL,
                        http_client=httpx.Client(
                            base_url=OPENROUTER_BASE_URL,
                            follow_redirects=True,
                            timeout=60.0,
                            headers={
                                "HTTP-Referer": "https://github.com/shitcoinsherpa/sherpa_bot",
                                "X-Title": "Sherpa Bot"
                            }
                        )
                    )
                    print("OpenRouter client initialized")
                
                # Update API provider preference
                self.api_provider = credentials.get('api_provider', 'openai')
'''
            content = content[:insert_pos] + openrouter_save_init + content[insert_pos:]
            print("✅ Updated save_credentials method")
    
    # Save the modified file
    with open('sherpa_bot.py', 'w') as f:
        f.write(content)
    
    print("\n✨ OpenRouter integration applied successfully!")
    print("\nNext steps:")
    print("1. Run the bot (./run.sh or run.bat)")
    print("2. Add your OpenRouter API key in the UI")
    print("3. Select 'OpenRouter' or 'Both' as your API provider")
    print("4. Add any custom OpenRouter models you want to use")
    print("5. Create characters using OpenRouter models")
    print("\n📖 See OPENROUTER_SETUP.md for detailed instructions")
    
    return True

if __name__ == "__main__":
    try:
        if apply_openrouter_integration():
            print("\n✅ Installation completed successfully!")
        else:
            print("\n❌ Installation failed or was cancelled")
    except Exception as e:
        print(f"\n❌ Error during installation: {e}")
        print("Please check the error and try again, or apply changes manually")
        print("See openrouter_integration.py for manual instructions")
