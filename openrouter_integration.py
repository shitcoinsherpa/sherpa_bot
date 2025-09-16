# OpenRouter Integration for Sherpa Bot
# This file contains the modifications needed to add OpenRouter support
# Apply these changes to your sherpa_bot.py file

# ============================================
# SECTION 1: Add these constants after the existing constants (around line 80)
# ============================================

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

# ============================================
# SECTION 2: Replace the TwitterBot.__init__ method
# ============================================

class TwitterBot:
    def __init__(self):
        print("\n=== Initializing TwitterBot ===")
        self.encryption_manager = EncryptionManager()
        self.credentials = {}
        self.characters = {}
        self.feed_config = {}
        self.openrouter_models = {}  # Store custom OpenRouter models
        self.scheduler_running = False
        self.current_topic = ""
        self.feed_index = 0
        self.tweet_queue = queue.Queue()
        self.tweet_count = 0
        self.last_tweet_time = None
        self.used_stories = set()
        self.recent_topics = []
        self.MAX_RECENT_TOPICS = 50
        self.feed_errors = defaultdict(int)
        self.feed_last_used = {}
        self.last_successful_tweet = None
        self.twitter_client = None
        self.backoff_until = None
        
        # Initialize meme-related variables
        self.use_memes = False
        self.meme_counter = 0
        self.meme_frequency = 5
        self.used_memes = set()
        
        # Create memes folder if it doesn't exist
        if not os.path.exists('memes'):
            os.makedirs('memes')
        
        # Rate limit tracking
        self.rate_limits = TWITTER_RATE_LIMITS.copy()
        
        # Load all configurations
        print("\n=== Loading Initial Data ===")
        self.credentials = self.load_credentials()
        print(f"Loaded credentials: {json.dumps({k: '[SET]' if v else '[EMPTY]' for k, v in self.credentials.items()}, indent=2)}")
        
        self.characters = self.load_characters()
        print(f"Loaded characters: {json.dumps(self.characters, indent=2)}")
        
        self.feed_config = self.load_feed_config()
        print(f"Loaded feed configuration: {json.dumps(self.feed_config, indent=2)}")
        
        self.openrouter_models = self.load_openrouter_models()
        print(f"Loaded OpenRouter models: {json.dumps(self.openrouter_models, indent=2)}")
        
        # Initialize API clients based on provider preference
        self.api_provider = self.credentials.get('api_provider', 'openai')  # Default to OpenAI for backward compatibility
        self.client = None
        self.openrouter_client = None
        
        # Initialize OpenAI client if credentials exist
        if self.credentials.get('openai_key'):
            self.client = OpenAI(
                api_key=self.credentials['openai_key'],
                http_client=httpx.Client(
                    base_url="https://api.openai.com/v1",
                    follow_redirects=True,
                    timeout=60.0
                )
            )
            print("OpenAI client initialized")
        
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
        
        # Initialize Twitter client if credentials exist
        if all(key in self.credentials for key in ['twitter_api_key', 'twitter_api_secret', 'twitter_access_token', 'twitter_access_token_secret']):
            self.twitter_client = tweepy.Client(
                consumer_key=self.credentials['twitter_api_key'],
                consumer_secret=self.credentials['twitter_api_secret'],
                access_token=self.credentials['twitter_access_token'],
                access_token_secret=self.credentials['twitter_access_token_secret']
            )
            print("Twitter client initialized")

    # ============================================
    # SECTION 3: Add these new methods to TwitterBot class
    # ============================================
    
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

    # ============================================
    # SECTION 4: Update the generate_tweet method
    # ============================================
    
    def generate_tweet(self, character_name, topic):
        character = self.characters.get(character_name)
        if not character:
            return None
            
        try:
            if self.tweet_count >= MAX_TWEETS_PER_MONTH:
                current_time = datetime.now()
                if not self.last_tweet_time or (current_time - self.last_tweet_time).days >= 30:
                    self.tweet_count = 0
                else:
                    return "Monthly tweet limit reached. Please wait for the next cycle."

            # Extract URL if present in the topic
            url_match = re.search(r'Read more: (https?://\S+)', topic)
            article_url = url_match.group(1) if url_match else None
            
            # Remove the "Read more: URL" part from the topic
            clean_topic = re.sub(r'\n\nRead more: https?://\S+', '', topic)

            # Calculate character limit
            TWITTER_SHORT_URL_LENGTH = 24
            max_content_length = 280 - TWITTER_SHORT_URL_LENGTH if article_url else 280

            # Add variation to prompt tone
            prompt_variants = [
                "Speak as if you're writing a soliloquy for a tragic sauce-themed play.",
                "Add a sprinkle of literary irony, but make it savory.",
                "Pretend to be distracted.",
                "Imagine you're writing from exile in a forgotten condiment aisle.",
                "Use language that suggests you're the last philosopher alive.",
                "Add an unexpected culinary metaphor, ideally involving vinegar or smoke.",
                "Maintain melancholy but make it tastefully funny.",
                "Respond as if the conversation was with a long lost friend.",
                "End with an awkward outro.",
            ]
            hour = datetime.now().hour
            if hour < 12:
                prompt_variants.append("Start with morning gloom, like breakfast with no sauce.")
            elif hour > 20:
                prompt_variants.append("Make it sound like a sauce-stained midnight confession.")

            variation = random.choice(prompt_variants)

            # Compose the prompt
            messages = [
                {"role": "system", "content": character['prompt']},
                {"role": "user", "content": f"{variation}\n\nCreate a tweet about this topic that is EXACTLY {max_content_length} characters or less. Make it engaging and maintain character voice. NO hashtags, emojis, or URLs - I'll add the URL later. Topic: {clean_topic}"}
            ]

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
            
            response = api_client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=200,
                temperature=1.0,
                presence_penalty=0.6,
                frequency_penalty=0.6
            )

            tweet_text = response.choices[0].message.content.strip()

            # Clean up quotation marks if present
            if tweet_text and len(tweet_text) >= 2:
                if (tweet_text[0] == '"' and tweet_text[-1] == '"') or \
                (tweet_text[0] == "'" and tweet_text[-1] == "'"):
                    tweet_text = tweet_text[1:-1].strip()

            # If tweet content is too long, try one more time with stricter length
            if len(tweet_text) > max_content_length:
                retry_messages = [
                    {"role": "system", "content": character['prompt']},
                    {"role": "user", "content": f"{variation}\n\nCreate a SHORTER tweet about this topic, maximum {max_content_length} characters. Be concise but maintain personality. NO hashtags, emojis, or URLs. Topic: {clean_topic}"}
                ]
                response = api_client.chat.completions.create(
                    model=model_name,
                    messages=retry_messages,
                    max_tokens=200,
                    temperature=1.0,
                    presence_penalty=0.6,
                    frequency_penalty=0.6
                )
                tweet_text = response.choices[0].message.content.strip()
                if tweet_text and len(tweet_text) >= 2:
                    if (tweet_text[0] == '"' and tweet_text[-1] == '"') or \
                    (tweet_text[0] == "'" and tweet_text[-1] == "'"):
                        tweet_text = tweet_text[1:-1].strip()

            # Truncate if still too long
            if len(tweet_text) > max_content_length:
                sentences = re.split(r'(?<=[.!?])\s+', tweet_text)
                truncated_text = ""
                for sentence in sentences:
                    if len(truncated_text + sentence) + 1 <= max_content_length:
                        truncated_text += " " + sentence if truncated_text else sentence
                    else:
                        break
                tweet_text = truncated_text.strip()

            # Append the article URL at the end
            if article_url:
                tweet_text = f"{tweet_text} {article_url}"

            self.tweet_count += 1
            self.last_tweet_time = datetime.now()

            return tweet_text

        except Exception as e:
            import traceback
            print(f"❌ Error generating tweet:")
            traceback.print_exc()
            return None

# ============================================
# SECTION 5: UI Updates - Add to create_ui() function
# ============================================

def create_ui_additions():
    """
    Add these components to the create_ui() function in the credentials section.
    Place them after the existing API key inputs.
    """
    
    # Add this after the OpenAI key input
    with gr.Row():
        api_provider = gr.Radio(
            choices=["OpenAI", "OpenRouter", "Both"],
            value=bot.credentials.get('api_provider', 'OpenAI'),
            label="API Provider",
            info="Choose which API provider to use for generating tweets"
        )
    
    with gr.Row():
        openrouter_key = gr.Textbox(
            label="OpenRouter API Key",
            type="password",
            show_label=True,
            container=True,
            scale=1,
            interactive=True,
            value=bot.credentials.get('openrouter_key', ''),
            info="Get your key from https://openrouter.ai/keys"
        )
    
    # Add OpenRouter Models Management section
    with gr.Accordion("🤖 OpenRouter Models", open=False):
        gr.Markdown("""
        Add custom OpenRouter models. Find model IDs at [OpenRouter Models](https://openrouter.ai/models).
        Format: `provider/model-name` (e.g., `anthropic/claude-3.5-sonnet`)
        """)
        
        with gr.Row():
            or_model_name = gr.Textbox(
                label="Display Name",
                placeholder="e.g., Claude 3.5 Sonnet",
                scale=1
            )
            or_model_id = gr.Textbox(
                label="Model ID",
                placeholder="e.g., anthropic/claude-3.5-sonnet",
                scale=1
            )
        
        with gr.Row():
            or_add_button = gr.Button("Add Model", variant="primary")
            or_remove_button = gr.Button("Remove Model", variant="secondary")
        
        or_model_list = gr.Dropdown(
            label="Current OpenRouter Models",
            choices=list(bot.openrouter_models.keys()),
            value=None,
            interactive=True
        )
        
        or_status = gr.Textbox(label="Status", interactive=False)
        
        def add_openrouter_model(display_name, model_id):
            if not display_name or not model_id:
                return "Please provide both display name and model ID", gr.update()
            
            models = bot.openrouter_models.copy()
            models[f"OpenRouter: {display_name}"] = {
                "name": model_id,
                "provider": "openrouter"
            }
            
            if bot.save_openrouter_models(models):
                return "Model added successfully", gr.update(choices=list(models.keys()))
            return "Failed to add model", gr.update()
        
        def remove_openrouter_model(model_key):
            if not model_key:
                return "Please select a model to remove", gr.update()
            
            if model_key in DEFAULT_OPENROUTER_MODELS:
                return "Cannot remove default models", gr.update()
            
            models = bot.openrouter_models.copy()
            if model_key in models:
                del models[model_key]
                if bot.save_openrouter_models(models):
                    return "Model removed successfully", gr.update(choices=list(models.keys()))
            return "Failed to remove model", gr.update()
        
        or_add_button.click(
            add_openrouter_model,
            inputs=[or_model_name, or_model_id],
            outputs=[or_status, or_model_list]
        )
        
        or_remove_button.click(
            remove_openrouter_model,
            inputs=[or_model_list],
            outputs=[or_status, or_model_list]
        )
    
    # Update the save_creds function to include new fields
    def save_creds_updated(key, api_key, api_secret, access_token, access_secret, 
                          telegram_token, telegram_chat, bearer_token,
                          api_provider, openrouter_key):
        
        print("\nSaving credentials...")
        credentials = {
            'openai_key': key,
            'twitter_api_key': api_key,
            'twitter_api_secret': api_secret,
            'twitter_access_token': access_token,
            'twitter_access_token_secret': access_secret,
            'telegram_bot_token': telegram_token,
            'telegram_chat_id': telegram_chat,
            'bearer_token': bearer_token,
            'api_provider': api_provider,
            'openrouter_key': openrouter_key
        }
        
        if bot.save_credentials(credentials):
            print("Credentials saved successfully")
            # Re-initialize clients if needed
            if openrouter_key and not bot.openrouter_client:
                bot.openrouter_client = OpenAI(
                    api_key=openrouter_key,
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
            return ("Credentials saved successfully",) + tuple(gr.update(value=v) for v in credentials.values())
        else:
            return ("Failed to save credentials",) + tuple(gr.update() for _ in range(len(credentials)))
    
    # Update model dropdown in Character Management
    # Replace the existing model_dropdown with:
    def update_model_dropdown():
        available_models = bot.get_available_models()
        model_dropdown = gr.Dropdown(
            label="Select Model",
            choices=list(available_models.keys()),
            value=list(available_models.keys())[0] if available_models else None,
            show_label=True,
            container=True,
            scale=1,
            interactive=True
        )
        return model_dropdown
    
    return {
        'api_provider': api_provider,
        'openrouter_key': openrouter_key,
        'save_creds_updated': save_creds_updated
    }

# ============================================
# SECTION 6: Update the save_credentials method
# ============================================

def save_credentials(self, credentials):
    print("\nSaving credentials to file...")
    print(f"Credentials to save: {list(credentials.keys())}")
    try:
        print("Encrypting credentials...")
        encrypted_data = self.encryption_manager.encrypt(credentials)
        if encrypted_data:
            print(f"Encrypted data length: {len(encrypted_data)} bytes")
            print("Writing to file...")
            with open(CREDENTIALS_FILE, 'wb') as f:
                f.write(encrypted_data)
            self.credentials = credentials
            print("Updated bot credentials in memory")
            
            # Update OpenAI client if key provided
            if credentials.get('openai_key'):
                print("Initializing OpenAI client...")
                self.client = OpenAI(
                    api_key=credentials['openai_key'],
                    http_client=httpx.Client(
                        base_url="https://api.openai.com/v1",
                        follow_redirects=True,
                        timeout=60.0
                    )
                )
                print("OpenAI client initialized")
            
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
            
            # Update Twitter client if all credentials provided
            if all(key in credentials for key in ['twitter_api_key', 'twitter_api_secret', 'twitter_access_token', 'twitter_access_token_secret']):
                print("Initializing Twitter client...")
                self.twitter_client = tweepy.Client(
                    consumer_key=credentials['twitter_api_key'],
                    consumer_secret=credentials['twitter_api_secret'],
                    access_token=credentials['twitter_access_token'],
                    access_token_secret=credentials['twitter_access_token_secret']
                )
                print("Twitter client initialized")
            
            # Update API provider preference
            self.api_provider = credentials.get('api_provider', 'openai')
            
            return True
        print("Failed to encrypt credentials")
        return False
    except Exception as e:
        print(f"Error saving credentials: {e}")
        import traceback
        traceback.print_exc()
        return False
