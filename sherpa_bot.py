import gradio as gr
from openai import OpenAI
import tweepy
import feedparser
import schedule
import time
import json
import threading
import queue
import os
from datetime import datetime, timedelta, timezone
from cryptography.fernet import Fernet
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import html2text
import httpx
import re
import random
from collections import defaultdict

# ------- Add these near your imports -------
import os, json, time, random
from datetime import datetime, timezone, timedelta

REPLY_STATE_FILE = "reply_state.json"
MAX_DAILY_REPLIES = 2
MAX_FETCH = 50
MAX_AGE_HOURS = 23
MAX_BACKLOG = 20   # store at most this many tweet IDs for tomorrow

def _load_reply_state():
    if os.path.exists(REPLY_STATE_FILE):
        with open(REPLY_STATE_FILE, "r") as f:
            return json.load(f)
    return {"last_post_day": None, "replied_today": 0, "since_id": None, "backlog": []}

def _save_reply_state(s):
    with open(REPLY_STATE_FILE, "w") as f:
        json.dump(s, f, indent=2)

def _parse_iso_z(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

def _age_hours(created_at: str) -> float:
    return (datetime.now(timezone.utc) - _parse_iso_z(created_at)).total_seconds() / 3600.0

def _score(public_metrics: dict) -> float:
    # Simple quality score; tweak as desired
    likes = public_metrics.get("like_count", 0)
    replies = public_metrics.get("reply_count", 0)
    rts = public_metrics.get("retweet_count", 0)
    return likes + 2 * replies + 0.5 * rts

def _prune_backlog(backlog: list) -> list:
    # Keep only unique tweet_ids that are still <23h; cap size
    seen = set()
    kept = []
    for item in backlog:
        tid = item.get("tweet_id")
        ts = item.get("created_at")
        if not tid or not ts or tid in seen:
            continue
        if _age_hours(ts) < MAX_AGE_HOURS:
            seen.add(tid)
            kept.append(item)
    return kept[:MAX_BACKLOG]
import random

def get_random_story_all(self):
    """Pick a random subject and return a story in the same shape as get_new_story()."""
    subjects = list(RSS_FEEDS.keys())  # e.g. ["crypto", "ai", "tech"]
    random.shuffle(subjects)
    for s in subjects:
        story = self.get_new_story(s)  # normal path for a real subject
        if story:
            # (optional) annotate where it came from
            story.setdefault("source_subject", s)
            return story
    return None


# Constants
ENCRYPTION_KEY_FILE = "encryption.key"
CREDENTIALS_FILE = "encrypted_credentials.bin"
CHARACTERS_FILE = "encrypted_characters.bin"
FEED_CONFIG_FILE = "encrypted_feed_config.bin"  # New file for feed selection
MAX_TWEETS_PER_MONTH = 500
TWEET_INTERVAL_HOURS = 1.5
FEED_TIMEOUT = 10  # seconds
FEED_ERROR_THRESHOLD = 5  # max consecutive errors before skipping feed
MIN_STORIES_PER_FEED = 2  # minimum stories to get from each feed
PRIMARY_FEED_WEIGHT = 2.0  # Weight multiplier for primary sources

# Constants for meme handling
SUPPORTED_MEME_FORMATS = ('.jpg', '.jpeg', '.png', '.gif')
USED_MEMES_HISTORY = 10  # How many recently used memes to remember

# Twitter API Rate Limits
TWITTER_RATE_LIMITS = {
    "tweets": {
        "endpoint": "statuses/update",
        "window_hours": 3,
        "max_tweets": 300,  # Combined limit for tweets and retweets
        "current_count": 0,
        "window_start": None,
        "reset_time": None,
        "backoff_until": None
    }
}

# Twitter API retry settings
TWITTER_RETRY_CONFIG = {
    "initial_backoff": 60,  # Start with 1 minute
    "max_backoff": 3600,    # Max 1 hour
    "backoff_factor": 2,    # Double each time
    "max_retries": 5
}

# Default headers for feed requests
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# OpenAI Models with limits
OPENAI_MODELS = {
    "gpt-3.5-turbo (Most affordable)": {
        "name": "gpt-3.5-turbo",
        "tpm": "10M tokens/min",
        "rpm": "10K requests/min"
    },
    "gpt-4o": {
        "name": "gpt-4o",
        "tpm": "2M tokens/min",
        "rpm": "10K requests/min"
    },
    "gpt-4o-mini": {
        "name": "gpt-4o-mini",
        "tpm": "10M tokens/min",
        "rpm": "10K requests/min"
    },
    "gpt-4": {
        "name": "gpt-4",
        "tpm": "300K tokens/min",
        "rpm": "10K requests/min"
    },
    "gpt-4-turbo": {
        "name": "gpt-4-turbo",
        "tpm": "800K tokens/min",
        "rpm": "10K requests/min"
    }
}

# RSS Feed Categories
RSS_FEEDS = {
    "crypto": {
        "primary": [
            {"url": "https://www.theblock.co/rss.xml", "name": "The Block"},
            {"url": "https://blog.kraken.com/feed", "name": "Kraken Blog"},
            {"url": "https://messari.io/rss", "name": "Messari"},
            {"url": "https://blockworks.co/feed", "name": "Blockworks"}
            # Removed Coin Bureau due to malformed feed
        ],
        "secondary": [
            {"url": "https://cointelegraph.com/rss", "name": "CoinTelegraph"},
            {"url": "https://cryptonews.com/news/feed/", "name": "CryptoNews"},
            {"url": "https://decrypt.co/feed", "name": "Decrypt"},
            {"url": "https://news.bitcoin.com/feed/", "name": "Bitcoin.com"},
            {"url": "https://coindesk.com/arc/outboundfeeds/rss/", "name": "CoinDesk"},
            {"url": "https://bitcoinmagazine.com/.rss/full/", "name": "Bitcoin Magazine"},
            {"url": "https://cryptopotato.com/feed/", "name": "CryptoPotato"},
            {"url": "https://ambcrypto.com/feed/", "name": "AMBCrypto"},
            {"url": "https://newsbtc.com/feed/", "name": "NewsBTC"},
            {"url": "https://cryptoslate.com/feed/", "name": "CryptoSlate"},
            {"url": "https://beincrypto.com/feed/", "name": "BeInCrypto"},
            {"url": "https://bitcoinist.com/feed/", "name": "Bitcoinist"},
            {"url": "https://dailyhodl.com/feed/", "name": "The Daily Hodl"}
        ]
    },
    "ai": {
        "primary": [
            {"url": "http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=lastUpdatedDate&sortOrder=descending&max_results=10", "name": "arXiv - Artificial Intelligence"},
            {"url": "http://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=lastUpdatedDate&sortOrder=descending&max_results=10", "name": "arXiv - Machine Learning"},
            {"url": "http://export.arxiv.org/api/query?search_query=cat:cs.CL&sortBy=lastUpdatedDate&sortOrder=descending&max_results=10", "name": "arXiv - Computation and Language"},
            {"url": "http://export.arxiv.org/api/query?search_query=cat:cs.CV&sortBy=lastUpdatedDate&sortOrder=descending&max_results=10", "name": "arXiv - Computer Vision"},
            {"url": "http://export.arxiv.org/api/query?search_query=cat:cs.NE&sortBy=lastUpdatedDate&sortOrder=descending&max_results=10", "name": "arXiv - Neural and Evolutionary Computing"}
        ],
        "secondary": [
            {"url": "https://blog.research.google/feeds/posts/default", "name": "Google Research Blog"},
            {"url": "https://openai.com/news/rss.xml", "name": "OpenAI Blog"},
            {"url": "https://aws.amazon.com/blogs/machine-learning/feed/", "name": "AWS ML Blog"},
            {"url": "https://techcommunity.microsoft.com/t5/ai-machine-learning-blog/rss", "name": "Microsoft AI Blog"},
            {"url": "https://engineering.fb.com/feed/", "name": "Meta Engineering Blog"}
        ]
    },
    "tech": {
        "primary": [
            {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
            {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
            {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index"},
            {"name": "WIRED", "url": "https://www.wired.com/feed/rss"},
            {"name": "Engadget", "url": "https://www.engadget.com/rss.xml"},
            {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/"},
        ],
        "secondary": [
            {"name": "Tom's Hardware", "url": "https://www.tomshardware.com/feeds/all"},
            {"name": "The Next Web", "url": "https://thenextweb.com/feed"},
        ]
},

}
def get_random_story_from(categories=None):
    # categories: list[str] or None => all
    pool = []
    if not categories:
        # all categories
        for lst in RSS_FEEDS.values():
            pool.extend(lst)
    else:
        for c in categories:
            pool.extend(RSS_FEEDS.get(c.lower(), []))
    if not pool:
        return None

    # try up to a few times in case a feed is temporarily empty
    for _ in range(4):
        name, url = random.choice(pool)
        feed = feedparser.parse(url)
        if feed.entries:
            entry = random.choice(feed.entries[:10])  # top few items
            title = getattr(entry, "title", "(untitled)")
            link = getattr(entry, "link", "")
            return f"{title} — {link}  \n(source: {name})"
    return None
class EncryptionManager:
    def __init__(self):
        self.key = None
        print("Initializing EncryptionManager...")

        # Load the encryption key if it exists
        if os.path.exists(ENCRYPTION_KEY_FILE):
            try:
                with open(ENCRYPTION_KEY_FILE, 'rb') as f:
                    self.key = f.read()
                    print(f"Loaded encryption key, length: {len(self.key)} bytes")
                    self.cipher = Fernet(self.key)
                    print("Successfully created Fernet cipher")
            except Exception as e:
                print(f"Error loading encryption key: {e}")
                traceback.print_exc()
                self.key = None

        # Validate the encryption key
        if self.key:
            self.validate_key()

        # Generate a new key if none exists
        if not self.key:
            print("Generating new encryption key...")
            self.key = Fernet.generate_key()
            try:
                with open(ENCRYPTION_KEY_FILE, 'wb') as f:
                    f.write(self.key)
                self.cipher = Fernet(self.key)
                print("Successfully generated and saved new key")
            except Exception as e:
                print(f"Error saving new encryption key: {e}")

    def validate_key(self):
        try:
            test_cipher = Fernet(self.key)
            test_message = b"Test message for encryption validation"
            encrypted_message = test_cipher.encrypt(test_message)
            decrypted_message = test_cipher.decrypt(encrypted_message)
            assert test_message == decrypted_message, "Decrypted message does not match original"
            print("Encryption key validation passed.")
        except Exception as validation_error:
            print(f"Encryption key validation failed: {validation_error}")
            traceback.print_exc()

    def encrypt(self, data):
        try:
            json_data = json.dumps(data)
            print(f"Encrypting data, JSON length: {len(json_data)}")
            encrypted = self.cipher.encrypt(json_data.encode())
            print(f"Successfully encrypted, length: {len(encrypted)} bytes")
            return encrypted
        except Exception as e:
            print(f"Error encrypting data: {e}")
            return None

    def decrypt(self, encrypted_data):
        try:
            print(f"Attempting to decrypt data, length: {len(encrypted_data)} bytes")
            decrypted = self.cipher.decrypt(encrypted_data)
            print("Successfully decrypted data")
            json_data = json.loads(decrypted.decode())
            print(f"Successfully parsed JSON, keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'not a dict'}")
            return json_data
        except Exception as e:
            print(f"Error decrypting data: {e}")
            traceback.print_exc()
            return {}

if __name__ == "__main__":
    manager = EncryptionManager()

class CryptoArticle:
    def __init__(self, title, preview, full_text, link, published_date):
        self.title = title
        self.preview = preview
        self.full_text = full_text
        self.link = link
        self.published_date = published_date
    
    def get_topic_text(self):
        return f"{self.title}\n\n{self.preview}"

class TwitterBot:
    def __init__(self):
        print("\n=== Initializing TwitterBot ===")
        self.encryption_manager = EncryptionManager()
        self.credentials = {}
        self.characters = {}
        self.feed_config = {}  # Store feed selection configuration
        self.scheduler_running = False
        self.current_topic = ""
        self.feed_index = 0
        self.tweet_queue = queue.Queue()
        self.tweet_count = 0
        self.last_tweet_time = None
        self.used_stories = set()  # Track used story URLs
        self.recent_topics = []    # Track recent topic keywords
        self.MAX_RECENT_TOPICS = 50  # Keep track of last 50 topics
        self.feed_errors = defaultdict(int)  # Track feed errors
        self.feed_last_used = {}  # Track when each feed was last used
        self.last_successful_tweet = None
        self.twitter_client = None  # Initialize Twitter client as None
        self.backoff_until = None

        # Initialize meme-related variables
        self.use_memes = False
        self.meme_counter = 0
        self.meme_frequency = 5  # Default: post meme every 5 tweets
        self.used_memes = set()  # Track recently used memes
        
        # Create memes folder if it doesn't exist
        if not os.path.exists('memes'):
            os.makedirs('memes')
        
        # Rate limit tracking
        self.rate_limits = TWITTER_RATE_LIMITS.copy()
        
        # Load all configurations
        print("\n=== Loading Initial Data ===")
        self.credentials = self.load_credentials()
        print(f"Loaded credentials: {json.dumps(self.credentials, indent=2)}")
        
        self.characters = self.load_characters()
        print(f"Loaded characters: {json.dumps(self.characters, indent=2)}")
        
        self.feed_config = self.load_feed_config()
        print(f"Loaded feed configuration: {json.dumps(self.feed_config, indent=2)}")
        
        # Initialize clients
        if self.credentials.get('openai_key'):
            self.client = OpenAI(
                api_key=self.credentials['openai_key'],
                http_client=httpx.Client(
                    base_url="https://api.openai.com/v1",
                    follow_redirects=True,
                    timeout=60.0
                )
            )
        
        if all(key in self.credentials for key in ['twitter_api_key', 'twitter_api_secret', 'twitter_access_token', 'twitter_access_token_secret']):
            self.twitter_client = tweepy.Client(
                consumer_key=self.credentials['twitter_api_key'],
                consumer_secret=self.credentials['twitter_api_secret'],
                access_token=self.credentials['twitter_access_token'],
                access_token_secret=self.credentials['twitter_access_token_secret']
            )
    def scheduler_worker(self):
        print("\n🛠️ Starting scheduler worker...")

        # Persist character/subject for auto-refill later
        self.scheduler_character = getattr(self, "scheduler_character", None)
        self.scheduler_subject = getattr(self, "scheduler_subject", "crypto")

        # State for cadence + daily reply window
        self.reply_bank = getattr(self, "reply_bank", [])
        self.last_daily_reply_date = getattr(self, "last_daily_reply_date", None)

        if not self.last_successful_tweet:
            print("🚀 No previous tweet timestamp found. Setting last_successful_tweet to now.")
            self.last_successful_tweet = datetime.now()

        while self.scheduler_running:
            try:
                # Respect any backoff
                if self.backoff_until and datetime.now() < self.backoff_until:
                    wait_seconds = (self.backoff_until - datetime.now()).total_seconds()
                    print(f"⏳ Backoff active until {self.backoff_until}. Sleeping {wait_seconds/60:.1f} minutes...")
                    time.sleep(min(60, max(1, wait_seconds)))
                    continue

                now = datetime.now()

                # === (1) Daily replies at ~10:00 AM, once per calendar day ===
                ten_am_today = now.replace(hour=10, minute=0, second=0, microsecond=0)
                if (self.last_daily_reply_date != now.date()) and (now >= ten_am_today):
                    print("\n📬 10:00 AM reached — checking mentions and replying to up to 2…")
                    handled = 0

                    # Use banked mentions first
                    pending = []
                    if self.reply_bank:
                        print(f"↪ Using {len(self.reply_bank)} banked mentions first.")
                        pending.extend(self.reply_bank)
                        self.reply_bank = []

                    if not pending:
                        fetched = []
                        try:
                            if hasattr(self, "collect_unreplied_mentions"):
                                fetched = self.collect_unreplied_mentions() or []
                            elif hasattr(self, "fetch_recent_mentions"):
                                fetched = self.fetch_recent_mentions() or []
                            elif hasattr(self, "monitor_and_reply_to_mentions"):
                                print("⚠ Using monitor_and_reply_to_mentions() fallback (may reply to more than 2).")
                                self.monitor_and_reply_to_mentions()
                                fetched = []
                            else:
                                print("⚠ No mention-collection method found.")
                                fetched = []
                        except Exception as e:
                            print(f"❌ Error fetching mentions: {e}")
                            fetched = []
                        pending.extend(fetched)

                    for m in pending:
                        if handled < 2:
                            try:
                                if hasattr(self, "reply_to_mention"):
                                    self.reply_to_mention(m)
                                    handled += 1
                                elif hasattr(self, "reply_to_engagement"):
                                    self.reply_to_engagement(m)
                                    handled += 1
                                else:
                                    self.reply_bank.append(m)
                                    print("⚠ No single-mention reply method; banking this mention.")
                            except Exception as e:
                                print(f"❌ Failed replying to a mention: {e}")
                        else:
                            self.reply_bank.append(m)

                    print(f"✅ Replied to {handled} mention(s). Banked {len(self.reply_bank)} leftover(s).")
                    self.last_daily_reply_date = now.date()

                # === (2) Main tweet every 4 hours ===
                if (now - self.last_successful_tweet).total_seconds() >= (4 * 3600):
                    print("\n⏰ 4 hours passed — preparing to send next tweet...")

                    if not self.tweet_queue.empty():
                        character, story_text, subject = self.tweet_queue.get()
                        tweet_text = self.generate_tweet(character, story_text)
                        if tweet_text and self.send_tweet(tweet_text):
                            print("✅ Tweet from queue sent.")
                            self.last_successful_tweet = datetime.now()

                            # Queue up the next story
                            next_story = self.get_new_story(subject)
                            if next_story:
                                next_text = f"{next_story['title']}\n\n{next_story.get('preview','')}\n\nRead more: {next_story['url']}"
                                self.tweet_queue.put((character, next_text, subject))
                        else:
                            print("❌ Failed to send tweet from queue.")
                    else:
                        print("📭 Tweet queue is empty — trying to refill...")
                        next_story = self.get_new_story(self.scheduler_subject)
                        if next_story:
                            next_text = f"{next_story['title']}\n\n{next_story.get('preview','')}\n\nRead more: {next_story['url']}"
                            self.tweet_queue.put((self.scheduler_character, next_text, self.scheduler_subject))
                            print("📥 Refilled tweet queue with a new story.")
                        else:
                            print("❌ Failed to get a new story. Queue remains empty.")

                time.sleep(30)

            except Exception as e:
                print(f"❌ Error in scheduler worker: {e}")
                time.sleep(60)

        
    def get_random_story_all(self, *args, **kwargs):
        """
        Compatibility alias so get_new_story() can call this.
        Routes to the existing get_random_story(...) if present.
        """
        if hasattr(self, "get_random_story"):
            return self.get_random_story(*args, **kwargs)
        # Fallback: nothing else to delegate to
        print("[get_random_story_all] No get_random_story(...) found; returning None.")
        return None

    def load_credentials(self):
        print("\nLoading credentials...")
        if not os.path.exists(CREDENTIALS_FILE):
            print("No credentials file found")
            return {}
        try:
            with open(CREDENTIALS_FILE, 'rb') as f:
                data = f.read()
                print(f"Read credentials file, size: {len(data)} bytes")
                if not data:
                    print("Empty credentials file")
                    return {}
                print("Attempting to decrypt credentials...")
                decrypted = self.encryption_manager.decrypt(data)
                if not decrypted:
                    print("Failed to decrypt credentials")
                    return {}
                print(f"Successfully loaded credentials with keys: {list(decrypted.keys())}")
                return decrypted
        except Exception as e:
            print(f"Error loading credentials: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def load_characters(self):
        print("\nLoading characters...")
        if not os.path.exists(CHARACTERS_FILE):
            print("No characters file found")
            return {}
        try:
            with open(CHARACTERS_FILE, 'rb') as f:
                data = f.read()
                print(f"Read characters file, size: {len(data)} bytes")
                if not data:
                    print("Empty characters file")
                    return {}
                print("Attempting to decrypt characters...")
                decrypted = self.encryption_manager.decrypt(data)
                if not decrypted:
                    print("Failed to decrypt characters")
                    return {}
                print(f"Successfully loaded characters with keys: {list(decrypted.keys())}")
                return decrypted
        except Exception as e:
            print(f"Error loading characters: {e}")
            import traceback
            traceback.print_exc()
            return {} 
    
    def load_character_prompt(char_name):
        if not char_name:
            return ""
        return bot.characters.get(char_name, {}).get('prompt', "")  
    
     # Get default character prompt
    character_prompt = gr.Textbox(
        label="Character System Prompt",
        lines=5,
        placeholder="Enter the system prompt that defines this character's personality...",
        value="",
        show_label=True,
        container=True,
        scale=1,
        interactive=True,
    )

    def get_assistant_details(self, assistant_id):
        """Fetch assistant details from OpenAI API v2"""
        try:
            if not self.client:
                return None, "OpenAI client not initialized. Please check your API key."

            headers = {
                "Authorization": f"Bearer {self.client.api_key}",
                "OpenAI-Beta": "assistants=v2"
            }
            url = f"https://api.openai.com/v1/assistants/{assistant_id}"

            print(f"Fetching assistant from URL: {url}")  # Log the URL
            response = httpx.get(url, headers=headers)

            print(f"Response status code: {response.status_code}") # Log status code
            print(f"Response headers: {response.headers}") # Log headers
            print(f"Response content: {response.text}") # Log content

            if response.status_code == 200:
                try:
                    assistant = response.json()
                    print(f"Successfully fetched assistant: {assistant.get('id')}") # Log successful fetch
                    print(f"Assistant Dictionary Structure: {assistant}") # Print the dictionary
                    return assistant, None
                except json.JSONDecodeError:
                    return None, "Error: Response is not valid JSON. Check response content."
            else:
                try:
                    error_message = response.json().get('error', {}).get('message', 'Unknown error')
                except json.JSONDecodeError:
                    error_message = f"Unknown error - Non-JSON response: {response.text}"
                return None, f"Error fetching assistant: Error code: {response.status_code} - {error_message}"

        except httpx.RequestError as e:
            return None, f"Request error: {e}"
        except Exception as e:
            return None, f"General error fetching assistant: {str(e)}"
    
    def save_character_from_assistant(self, name, assistant_id):
        """Create a character from an OpenAI assistant"""
        try:
            assistant, error = self.get_assistant_details(assistant_id)
            if error:
                return False, error
            
            characters = self.characters.copy()
            characters[name] = {
                'prompt': assistant['instructions'],
                'model': assistant['model'],
                'assistant_id': assistant_id  # Store the assistant ID for future reference
            }
            
            if self.save_characters(characters):
                return True, "Character created successfully from assistant"
            return False, "Failed to save character"
            
        except Exception as e:
            return False, f"Error creating character: {str(e)}"    
    
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
                
                return True
            print("Failed to encrypt credentials")
            return False
        except Exception as e:
            print(f"Error saving credentials: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save_characters(self, characters):
        print("\nSaving characters to file...")
        print(f"Characters to save: {list(characters.keys())}")
        try:
            print("Encrypting characters...")
            encrypted_data = self.encryption_manager.encrypt(characters)
            if encrypted_data:
                print(f"Encrypted data length: {len(encrypted_data)} bytes")
                print("Writing to file...")
                with open(CHARACTERS_FILE, 'wb') as f:
                    f.write(encrypted_data)
                self.characters = characters
                print("Updated bot characters in memory")
                return True
            print("Failed to encrypt characters")
            return False
        except Exception as e:
            print(f"Error saving characters: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_article_content(self, url):
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text(separator='\n', strip=True)
            return text
        except:
            return ""

    def extract_keywords(self, text):
        """Extract important keywords from text to track topic diversity"""
        # Common crypto terms to ignore
        common_terms = {'crypto', 'blockchain', 'bitcoin', 'ethereum', 'btc', 'eth', 
                       'cryptocurrency', 'cryptocurrencies', 'token', 'tokens', 'defi',
                       'market', 'markets', 'trading', 'price', 'prices'}
        
        # Split into words and clean
        words = re.findall(r'\b\w+\b', text.lower())
        # Remove common terms, short words, and numbers
        keywords = {word for word in words 
                   if word not in common_terms 
                   and len(word) > 3 
                   and not word.isdigit()}
        return keywords

    def is_similar_to_recent(self, title, preview):
        """Check if a story is too similar to recently posted ones"""
        # Extract keywords from new story
        new_keywords = self.extract_keywords(f"{title} {preview}")
        
        # Compare with recent topics
        for recent_keywords in self.recent_topics:
            # If more than 40% of keywords overlap, consider it too similar
            overlap = len(new_keywords & recent_keywords) / len(new_keywords | recent_keywords)
            if overlap > 0.4:
                return True
        return False

    def get_arxiv_paper_details(self, url):
        """Get detailed information about an arXiv paper including abstract and authors."""
        try:
            # Convert URL to API URL
            paper_id = url.split('/')[-1]
            if 'arxiv.org/abs/' in url:
                paper_id = url.split('arxiv.org/abs/')[-1]
            elif 'arxiv.org/pdf/' in url:
                paper_id = url.split('arxiv.org/pdf/')[-1].replace('.pdf', '')
            
            api_url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
            
            response = requests.get(api_url, timeout=FEED_TIMEOUT)
            response.raise_for_status()
            
            # Parse the XML response
            from xml.etree import ElementTree
            root = ElementTree.fromstring(response.content)
            
            # arXiv API uses namespaces
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            entry = root.find('.//atom:entry', ns)
            if entry is not None:
                abstract = entry.find('atom:summary', ns).text.strip()
                authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
                categories = [cat.get('term') for cat in entry.findall('atom:category', ns)]
                
                # Get HTML link (not PDF) for better preview cards
                links = entry.findall('atom:link', ns)
                html_url = next((link.get('href') for link in links if link.get('type') == 'text/html'), None)
                if not html_url:
                    # Construct HTML URL from paper ID
                    html_url = f"https://arxiv.org/abs/{paper_id}"
                
                return {
                    'abstract': abstract,
                    'authors': authors,
                    'categories': categories,
                    'html_url': html_url,
                    'paper_id': paper_id
                }
        except Exception as e:
            print(f"Error fetching arXiv paper details: {e}")
        return None

    def load_feed_config(self):
        """Load feed configuration from file"""
        try:
            if os.path.exists('feed_config.json'):
                with open('feed_config.json', 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading feed configuration: {e}")
            return {}
    
    def save_feed_config(self, config):
        """Save feed configuration to file"""
        try:
            with open('feed_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            self.feed_config = config
            return True
        except Exception as e:
            print(f"Error saving feed configuration: {e}")
            return False
    
    def get_new_story(self, subject):
        """Get a new story from RSS feeds based on subject"""

        # --- Handle Surprise/unknown subjects up front ---
        if subject in ("__surprise_all__", "surprise", "random", None, ""):
            return self.get_random_story_all()
        if subject not in RSS_FEEDS:
            print(f"⚠️ Unknown subject '{subject}'. Falling back to random.")
            return self.get_random_story_all()

        # Get enabled feeds based on configuration
        feed_config = self.feed_config.get(subject, {})
        subject_feeds = RSS_FEEDS.get(subject, {})

        # Safely get lists (default to empty if keys missing)
        all_primary = subject_feeds.get("primary", [])
        all_secondary = subject_feeds.get("secondary", [])

        # Filter primary feeds based on configuration
        primary_feeds = [
            feed for feed in all_primary
            if feed_config.get("primary", {}).get(feed["url"], True)  # Default to True if not configured
        ]

        # Filter secondary feeds based on configuration
        secondary_feeds = [
            feed for feed in all_secondary
            if feed_config.get("secondary", {}).get(feed["url"], True)  # Default to True if not configured
        ]

        # If config disables everything, fall back to all feeds for this subject
        if not primary_feeds and not secondary_feeds:
            print("ℹ️ No feeds enabled by config; falling back to all feeds for this subject.")
            primary_feeds, secondary_feeds = all_primary, all_secondary

        # Time windows to try, in order of preference (in hours)
        time_windows = [
            {"hours": 24, "entries": []},   # Last 24 hours
            {"hours": 48, "entries": []},   # Last 2 days
            {"hours": 72, "entries": []},   # Last 3 days
            {"hours": 120, "entries": []}   # Last 5 days
        ]

        # Collect stories from all feeds for each time window
        for time_window in time_windows:
            # Try primary feeds first
            for feed in primary_feeds:
                try:
                    stories = self.get_stories_from_feed(feed, time_window)
                    if stories:
                        time_window["entries"].extend(stories)
                except Exception as e:
                    print(f"Error fetching from primary feed {feed.get('url')}: {e}")

            # Then try secondary feeds
            for feed in secondary_feeds:
                try:
                    stories = self.get_stories_from_feed(feed, time_window)
                    if stories:
                        time_window["entries"].extend(stories)
                except Exception as e:
                    print(f"Error fetching from secondary feed {feed.get('url')}: {e}")

            # If we found stories in this time window, sort by recency and pick one
            if time_window["entries"]:
                print(f"\nFound {len(time_window['entries'])} total stories within {time_window['hours']} hours")
                # Sort all entries by recency
                time_window["entries"].sort(key=lambda x: x['time_since_pub'])
                # Pick randomly from the most recent stories (up to 5)
                selection_pool = time_window["entries"][:5]
                selected = random.choice(selection_pool)

                # Track this story
                self.used_stories.add(selected['url'])
                if len(self.used_stories) > 200:
                    self.used_stories.pop()

                # Track topic keywords
                new_keywords = self.extract_keywords(f"{selected['title']} {selected['preview']}")
                self.recent_topics.append(new_keywords)
                if len(self.recent_topics) > self.MAX_RECENT_TOPICS:
                    self.recent_topics.pop(0)

                print(f"Selected story from {selected['source']}")
                print(f"Title: {selected['title']}")
                print(f"Published {selected['time_since_pub']:.1f} hours ago")
                return selected

        return None

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

            # 🔀 Add variation to prompt tone
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

            # 🧠 Compose the prompt
            messages = [
                {"role": "system", "content": character['prompt']},
                {"role": "user", "content": f"{variation}\n\nCreate a tweet about this topic that is EXACTLY {max_content_length} characters or less. Make it engaging and maintain character voice. NO hashtags, emojis, or URLs - I'll add the URL later. Topic: {clean_topic}"}
            ]

            response = self.client.chat.completions.create(
                model=character['model'],
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
                response = self.client.chat.completions.create(
                    model=character['model'],
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

    def check_rate_limit(self):
        """Check if we're within rate limits for tweeting"""
        current_time = datetime.now()
        
        # Check if we're in backoff
        if self.rate_limits["tweets"]["backoff_until"]:
            if current_time < self.rate_limits["tweets"]["backoff_until"]:
                wait_seconds = (self.rate_limits["tweets"]["backoff_until"] - current_time).total_seconds()
                print(f"\nIn backoff period. Waiting {wait_seconds/60:.1f} minutes")
                return False
            else:
                print("\nBackoff period ended, resetting rate limits")
                self.rate_limits["tweets"]["backoff_until"] = None
                self.rate_limits["tweets"]["current_count"] = 0
                self.rate_limits["tweets"]["window_start"] = current_time
                return True
        
        # Initialize window if needed
        if not self.rate_limits["tweets"]["window_start"]:
            self.rate_limits["tweets"]["window_start"] = current_time
            self.rate_limits["tweets"]["current_count"] = 0
            return True
        
        # Check if window has expired
        window_hours = self.rate_limits["tweets"]["window_hours"]
        window_start = self.rate_limits["tweets"]["window_start"]
        if (current_time - window_start).total_seconds() > window_hours * 3600:
            # Reset window
            self.rate_limits["tweets"]["window_start"] = current_time
            self.rate_limits["tweets"]["current_count"] = 0
            print("\nRate limit window reset")
            return True
        
        # Check if we're within limits
        if self.rate_limits["tweets"]["current_count"] < self.rate_limits["tweets"]["max_tweets"]:
            remaining = self.rate_limits["tweets"]["max_tweets"] - self.rate_limits["tweets"]["current_count"]
            print(f"\nRate limit status:")
            print(f"  Remaining: {remaining}")
            print(f"  Window started: {window_start}")
            print(f"  Window ends: {window_start + timedelta(hours=window_hours)}")
            return True
        
        # Calculate time until window reset
        reset_time = window_start + timedelta(hours=window_hours)
        wait_seconds = (reset_time - current_time).total_seconds()
        print(f"\nRate limit reached. Window resets in {wait_seconds/3600:.1f} hours")
        print(f"Current count: {self.rate_limits['tweets']['current_count']}")
        print(f"Window started: {window_start}")
        print(f"Window ends: {reset_time}")
        return False

    def handle_rate_limit_error(self, e):
        """Handle rate limit error with exponential backoff"""
        current_time = datetime.now()
        
        # Get reset time from headers if available
        if hasattr(e, 'response') and e.response is not None:
            reset_time = e.response.headers.get('x-rate-limit-reset')
            if reset_time:
                reset_datetime = datetime.fromtimestamp(int(reset_time))
                wait_seconds = (reset_datetime - current_time).total_seconds()
            else:
                # If no reset time in headers, use exponential backoff
                current_backoff = self.rate_limits["tweets"].get("current_backoff", TWITTER_RETRY_CONFIG["initial_backoff"])
                wait_seconds = min(current_backoff * TWITTER_RETRY_CONFIG["backoff_factor"], 
                                 TWITTER_RETRY_CONFIG["max_backoff"])
                self.rate_limits["tweets"]["current_backoff"] = wait_seconds
        else:
            # No response headers, use exponential backoff
            current_backoff = self.rate_limits["tweets"].get("current_backoff", TWITTER_RETRY_CONFIG["initial_backoff"])
            wait_seconds = min(current_backoff * TWITTER_RETRY_CONFIG["backoff_factor"], 
                             TWITTER_RETRY_CONFIG["max_backoff"])
            self.rate_limits["tweets"]["current_backoff"] = wait_seconds
        
        backoff_until = current_time + timedelta(seconds=wait_seconds)
        self.rate_limits["tweets"]["backoff_until"] = backoff_until
        
        print(f"\nRate limit exceeded. Implementing backoff:")
        print(f"  Wait time: {wait_seconds/60:.1f} minutes")
        print(f"  Resume at: {backoff_until}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response status: {e.response.status_code}")
            print(f"  Headers: {dict(e.response.headers)}")
        
        return wait_seconds

    def update_rate_limit(self):
        """Update rate limit counters after successful tweet"""
        self.rate_limits["tweets"]["current_count"] += 1
        print(f"\nUpdated rate limit count: {self.rate_limits['tweets']['current_count']}")
        print(f"Remaining in window: {self.rate_limits['tweets']['max_tweets'] - self.rate_limits['tweets']['current_count']}")

    def send_main_tweet(self):
        """Send a main scheduled tweet."""
        new_story = self.get_new_story("crypto")  # or "ai", depending on your subject
        if new_story:
            story_text = f"{new_story['title']}\n\n{new_story['preview']}\n\nRead more: {new_story['url']}"
            tweet_text = self.generate_tweet("mork zuckerbarge", story_text)
            if tweet_text:
                if self.send_tweet(tweet_text):
                    self.last_successful_tweet = datetime.now()
                    print("✅ Main tweet sent successfully.")
                else:
                    print("❌ Failed to send main tweet.")

    def reply_to_mentions_and_replies(self):
        if self.backoff_until and datetime.now() < self.backoff_until:
            print(f"⏳ Backoff active until {self.backoff_until}. Skipping mention/reply checking.")
            return

        print("🔍 Checking mentions and replies...")

        replies_sent = 0
        max_replies = 1
        
        print("🔍 Checking mentions and replies...")

        replies_sent = 0
        max_replies = 1

        try:
            mentions = self.twitter_client.get_users_mentions(self.mork_id, max_results=10)

            if mentions.data:
                for mention in mentions.data:
                    if replies_sent >= max_replies:
                        break
                    if mention.author_id == self.mork_id:
                        continue  # Skip replying to ourselves

                    prompt = f"Someone mentioned you: \"{mention.text}\""
                    reply = self.generate_tweet("mork zuckerbarge", prompt)

                    if reply:
                        self.twitter_client.create_tweet(
                            text=reply,
                            in_reply_to_tweet_id=mention.id
                        )
                        print(f"💬 Replied to {mention.id}")
                        replies_sent += 1

        except tweepy.TooManyRequests as e:
            print("🚫 Rate limited! Setting global backoff...")

            if hasattr(e, 'response') and e.response is not None:
                reset_timestamp = e.response.headers.get('x-rate-limit-reset')
                if reset_timestamp:
                    reset_time = datetime.fromtimestamp(int(reset_timestamp))
                    self.backoff_until = reset_time
                    wait_seconds = (reset_time - datetime.now()).total_seconds()
                    print(f"😴 Global backoff active until {self.backoff_until} (about {wait_seconds//60:.1f} min)")
                    time.sleep(min(300, wait_seconds))  # Sleep max 5 min chunks so you can still process local stuff
                    return False
            else:
                print("⚡ No reset time provided. Defaulting to 5 min backoff.")
                self.backoff_until = datetime.now() + timedelta(minutes=5)
                time.sleep(300)
                return False


        except Exception as e:
            print(f"❌ Error replying to mentions: {e}")
    def monitor_and_reply_to_engagement(self):
        self.monitor_and_reply_to_mentions()

    def send_tweet(self, tweet_text):
        if self.backoff_until and datetime.now() < self.backoff_until:
            print(f"⏳ Backoff active until {self.backoff_until}. Skipping sending tweet.")
            return False

    # (rest of your send_tweet code goes here...)


        if not self.check_rate_limit():
            print("Tweet skipped due to rate limit")
            return False

        try:
            client = tweepy.Client(
                consumer_key=self.credentials['twitter_api_key'],
                consumer_secret=self.credentials['twitter_api_secret'],
                access_token=self.credentials['twitter_access_token'],
                access_token_secret=self.credentials['twitter_access_token_secret'],
                wait_on_rate_limit=True
            )

            # Extract URL from tweet text and ensure it's at the end
            url_match = re.search(r'(https?://\S+)$', tweet_text)
            if url_match:
                url = url_match.group(1)
                tweet_text = re.sub(r'\s*' + re.escape(url) + r'\s*', '', tweet_text).strip()
                tweet_text = f"{tweet_text}\n\n{url}"

            print(f"\nSending tweet: {tweet_text}")

            response = client.create_tweet(text=tweet_text)

            if response.data:
                self.last_successful_tweet = datetime.now()
                print("\nTweet sent successfully")
                print(f"Tweet ID: {response.data['id']}")
                print(f"Response data: {response.data}")

                tweet_id = response.data['id']
                username = self.credentials.get("twitter_username", "zuckerbarge")
                tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
                self.send_to_telegram(tweet_url)

                self.update_rate_limit()
                return True

            print("\nTweet failed - no response data")
            return False

        except Exception as e:
            print(f"\nError sending tweet: {e}")
            return False


            # Update rate limit tracking
            self.update_rate_limit()
            return True
            
            print("\nTweet failed - no response data")
            print(f"Response object: {response}")
            return False
            
        except tweepy.TooManyRequests as e:
            print("🚫 Rate limited! Checking Twitter reset time...")

            if hasattr(e, 'response') and e.response is not None:
                reset_timestamp = e.response.headers.get('x-rate-limit-reset')
                if reset_timestamp:
                    reset_time = datetime.fromtimestamp(int(reset_timestamp))
                    now = datetime.now()
                    wait_seconds = (reset_time - now).total_seconds()

                    if wait_seconds > 0:
                        print(f"😴 Sleeping for {wait_seconds//60:.1f} minutes until rate limit resets...")
                        time.sleep(wait_seconds + 5)  # plus 5 second buffer
                        return
            else:
                print("⚡ No reset time found. Sleeping 5 minutes as fallback.")
                time.sleep(300)
                return

            
        except tweepy.TooManyRequests as e:
            print("🚫 Rate limited! Setting global backoff...")

            if hasattr(e, 'response') and e.response is not None:
                reset_timestamp = e.response.headers.get('x-rate-limit-reset')
                if reset_timestamp:
                    reset_time = datetime.fromtimestamp(int(reset_timestamp))
                    self.backoff_until = reset_time
                    wait_seconds = (reset_time - datetime.now()).total_seconds()
                    print(f"😴 Global backoff active until {self.backoff_until} (about {wait_seconds//60:.1f} min)")
                    time.sleep(min(300, wait_seconds))  # Sleep max 5 min chunks so you can still process local stuff
                    return False
            else:
                print("⚡ No reset time provided. Defaulting to 5 min backoff.")
                self.backoff_until = datetime.now() + timedelta(minutes=5)
                time.sleep(300)
                return False



            
        except Exception as e:
            print(f"\nError sending tweet: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_random_meme(self, character_name):
        """Get a random meme and generate a contextual tweet based on the filename"""
        try:
            # Get all memes for this character
            meme_files = [f for f in os.listdir('memes') if f.lower().endswith(tuple(SUPPORTED_MEME_FORMATS))]
            if not meme_files:
                return None, None
                
            # Select a random meme that hasn't been used recently
            available_memes = [m for m in meme_files if m not in self.used_memes]
            if not available_memes:
                self.used_memes.clear()  # Reset if all memes have been used
                available_memes = meme_files
                
            selected_meme = random.choice(available_memes)
            meme_path = os.path.join('memes', selected_meme)
            
            # Add to used memes
            self.used_memes.add(selected_meme)
            if len(self.used_memes) > USED_MEMES_HISTORY:
                self.used_memes.pop()
            
            # Extract context from filename
            # Remove extension and convert to readable format
            context = selected_meme.rsplit('.', 1)[0].replace('-', ' ')
            
            # Generate tweet based on meme context
            prompt = f"Create a tweet that perfectly matches this meme scenario: {context}. Make it funny and engaging while maintaining character voice. NO hashtags or URLs."
            
            response = self.client.chat.completions.create(
                model=self.characters[character_name]['model'],
                messages=[
                    {"role": "system", "content": self.characters[character_name]['prompt']},
                    {"role": "user", "content": prompt}
                ],
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
            
            return tweet_text, meme_path
            
        except Exception as e:
            print(f"Error getting random meme: {e}")
            return None, None

    def send_tweet_with_media(self, tweet_text, media_path):
        """Send a tweet with media attached"""
        try:
            # Create Twitter API v1.1 instance for media upload
            auth = tweepy.OAuth1UserHandler(
                self.credentials['twitter_api_key'],
                self.credentials['twitter_api_secret'],
                self.credentials['twitter_access_token'],
                self.credentials['twitter_access_token_secret']
            )
            api = tweepy.API(auth)
            
            # Upload media
            media = api.media_upload(filename=media_path)
            
            # Create tweet with media using v2 client
            response = self.twitter_client.create_tweet(
                text=tweet_text,
                media_ids=[media.media_id]
            )
            
            if response.data:
                self.last_successful_tweet = datetime.now()
                print("\nTweet with media sent successfully")
                print(f"Tweet ID: {response.data['id']}")
                
                # Update rate limit tracking
                self.update_rate_limit()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error sending tweet with media: {e}")
            return False
            
    def send_to_telegram(self, tweet_url):
        bot_token = self.credentials.get("telegram_bot_token")
        chat_id = self.credentials.get("telegram_chat_id")

        if not bot_token or not chat_id:
            print("⚠️ Telegram credentials missing")
            return

        text = f"Mork has tweeted:\n{tweet_url}"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(url, data=payload)
            print("📨 Telegram status:", response.status_code, response.text)
        except Exception as e:
            print(f"❌ Telegram send failed: {e}")
    import requests  # Make sure you have this imported at top

    def monitor_and_reply_to_mentions(self):
        """Daily: fetch new mentions, pick best <=2 <23h old, reply; try backlog first."""
        try:
            print("\n🔍 Daily mention sweep starting...")

            bearer_token = self.credentials.get('bearer_token')
            if not bearer_token:
                print("❌ Bearer token missing. Cannot check mentions.")
                return

            state = _load_reply_state()
            today = datetime.now(timezone.utc).date().isoformat()

            # Daily counter/reset
            if state.get("last_post_day") != today:
                state["last_post_day"] = today
                state["replied_today"] = 0

            remaining = MAX_DAILY_REPLIES - state["replied_today"]
            if remaining <= 0:
                print("✅ Daily reply cap already reached.")
                _save_reply_state(state)
                return

            headers = {"Authorization": f"Bearer {bearer_token}"}
            me = self.twitter_client.get_me().data
            me_id = str(me.id)

            # 1) Try backlog first (tweet_ids we saved yesterday), keeping only <23h
            backlog = _prune_backlog(state.get("backlog", []))
            sent = 0
            i = 0
            while i < len(backlog) and sent < remaining:
                draft = backlog[i]
                tid = draft["tweet_id"]
                # (Optional) cheap recheck via v2 tweets lookup to ensure it's still valid
                try:
                    # generate fresh text now (cheaper than storing text that may expire)
                    text = self.generate_persona_reply_from_tweet_id(tid) if hasattr(self, "generate_persona_reply_from_tweet_id") else None
                    if not text:
                        # Fallback: fetch tweet text to pass to persona
                        tw_resp = requests.get(
                            "https://api.twitter.com/2/tweets",
                            headers=headers,
                            params={"ids": tid, "tweet.fields": "text"}
                        )
                        tw_json = tw_resp.json()
                        tw_text = (tw_json.get("data") or [{}])[0].get("text", "")
                        if not tw_text:
                            i += 1
                            continue
                        character = next(iter(self.characters.values()))
                        ai = self.client.chat.completions.create(
                            model=character['model'],
                            messages=[
                                {"role": "system", "content": character['prompt']},
                                {"role": "user", "content": f"Reply in character to this mention: '{tw_text}'"}
                            ],
                            max_tokens=180,
                            temperature=0.9,
                        )
                        text = ai.choices[0].message.content.strip()

                    self.twitter_client.create_tweet(text=text, in_reply_to_tweet_id=tid)
                    print(f"✅ Replied from backlog → {tid}")
                    state["replied_today"] += 1
                    sent += 1
                    backlog.pop(i)
                    time.sleep(random.uniform(4, 9))
                except Exception as e:
                    print(f"⚠️ Backlog reply failed for {tid}: {e}")
                    i += 1  # skip this one

            if state["replied_today"] >= MAX_DAILY_REPLIES:
                state["backlog"] = backlog
                _save_reply_state(state)
                print(f"🎯 Done from backlog only. Replied {sent}.")
                return

            # 2) Fetch new mentions once; only what we need
            url = f"https://api.twitter.com/2/users/{me_id}/mentions"
            params = {
                "max_results": min(100, MAX_FETCH),
                "tweet.fields": "author_id,text,created_at,public_metrics,lang",
            }
            # since_id keeps read calls tiny and prevents reprocessing old mentions
            if state.get("since_id"):
                params["since_id"] = state["since_id"]

            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                print(f"❌ Error fetching mentions: {resp.status_code} {resp.text}")
                state["backlog"] = backlog  # keep backlog progress
                _save_reply_state(state)
                return

            data = resp.json().get("data", []) or []
            if data:
                # high-water mark so we never reread older mentions
                state["since_id"] = max(data, key=lambda t: int(t["id"]))["id"]

            # Filter viable: not self, English (if present), <23h, basic effort
            candidates = []
            for tw in data:
                if str(tw.get("author_id")) == me_id:
                    continue
                if tw.get("lang") and tw["lang"].lower() != "en":
                    continue
                if _age_hours(tw["created_at"]) >= MAX_AGE_HOURS:
                    continue
                if len((tw.get("text") or "").strip()) < 8:
                    continue
                candidates.append(tw)

            if not candidates and sent == 0:
                print("ℹ️ No new viable mentions.")
                state["backlog"] = backlog
                _save_reply_state(state)
                return

            # Rank by public engagement
            candidates.sort(key=lambda t: _score(t.get("public_metrics") or {}), reverse=True)

            remaining = MAX_DAILY_REPLIES - state["replied_today"]
            to_post = candidates[:remaining]
            # Bank the rest (IDs only; we'll generate text next run if still fresh)
            for extra in candidates[remaining:]:
                backlog.append({"tweet_id": extra["id"], "created_at": extra["created_at"]})

            # 3) Generate + post replies for top picks
            for tw in to_post:
                try:
                    character = next(iter(self.characters.values()))
                    ai = self.client.chat.completions.create(
                        model=character['model'],
                        messages=[
                            {"role": "system", "content": character['prompt']},
                            {"role": "user", "content": f"Reply to this mention in character: '{tw['text']}'"}
                        ],
                        max_tokens=180,
                        temperature=0.9,
                    )
                    reply_text = ai.choices[0].message.content.strip()

                    self.twitter_client.create_tweet(
                        text=reply_text,
                        in_reply_to_tweet_id=tw["id"]
                    )
                    print(f"✅ Replied to {tw['id']}")
                    state["replied_today"] += 1
                    time.sleep(random.uniform(4, 9))
                except Exception as e:
                    print(f"⚠️ Failed to reply to {tw.get('id')}: {e}")
                    # If posting fails, keep it as a backlog item for next run
                    backlog.append({"tweet_id": tw["id"], "created_at": tw["created_at"]})

            # Finalize state
            state["backlog"] = _prune_backlog(backlog)
            _save_reply_state(state)
            print(f"🎯 Daily sweep complete. Replied {state['replied_today']} today; backlog={len(state['backlog'])}.")

        except Exception as e:
            print(f"❌ Fatal error in mention reply worker: {e}")



def save_feed_selection(subject, primary_selected, secondary_selected):
    """Save the selected feeds configuration"""
    print(f"\nSaving feed selection for subject: {subject}")
    print(f"Primary selected: {primary_selected}")
    print(f"Secondary selected: {secondary_selected}")
    
    try:
        # Get current feed config
        config = bot.feed_config.copy()
        if subject not in config:
            config[subject] = {"primary": {}, "secondary": {}}
        
        # Update primary feeds
        primary_feeds = RSS_FEEDS[subject]["primary"]
        for feed in primary_feeds:
            feed_name = f"{feed['name']} ({feed['url']})"
            config[subject]["primary"][feed["url"]] = feed_name in primary_selected
        
        # Update secondary feeds
        secondary_feeds = RSS_FEEDS[subject]["secondary"]
        for feed in secondary_feeds:
            feed_name = f"{feed['name']} ({feed['url']})"
            config[subject]["secondary"][feed["url"]] = feed_name in secondary_selected
        
        # Save configuration
        if bot.save_feed_config(config):
            print("Feed configuration saved successfully")
            print(f"New config: {json.dumps(config, indent=2)}")
            return "Feed configuration saved successfully"
        
        print("Failed to save feed configuration")
        return "Failed to save feed configuration"
    
    except Exception as e:
        print(f"Error saving feed selection: {e}")
        import traceback
        traceback.print_exc()
        return f"Error saving feed configuration: {str(e)}"

def create_ui():
    print("\n=== Creating UI ===")
    global bot  # Make bot instance globally accessible
    bot = TwitterBot()
    bot.last_successful_tweet = datetime.now()

    
    print("\nUI Initial State:")
    print(f"Credentials available: {list(bot.credentials.keys())}")
    for key, value in bot.credentials.items():
        print(f"{key}: {'[SET]' if value else '[EMPTY]'} (length: {len(value) if value else 0})")
    
    print(f"\nCharacters available: {list(bot.characters.keys())}")
    for char_name, char_data in bot.characters.items():
        print(f"Character '{char_name}':")
        print(f"  - Prompt length: {len(char_data['prompt']) if 'prompt' in char_data else 0}")
        print(f"  - Model: {char_data.get('model', 'not set')}")
    
    # Store initial values
    initial_values = {
        'openai_key': bot.credentials.get('openai_key', ''),
        'twitter_api_key': bot.credentials.get('twitter_api_key', ''),
        'twitter_api_secret': bot.credentials.get('twitter_api_secret', ''),
        'twitter_access_token': bot.credentials.get('twitter_access_token', ''),
        'twitter_access_token_secret': bot.credentials.get('twitter_access_token_secret', '')
    }

    with gr.Blocks(theme=gr.themes.Soft(
        primary_hue="green",
        secondary_hue="green",
        neutral_hue="slate",
        text_size="lg",
    )) as interface:
        print("\n=== Creating UI Components ===")
        gr.Markdown("# 💻 AI Twitter Bot Control Center")
        
        with gr.Accordion("🔑 Getting Started", open=True):
            gr.Markdown("""
            1. OpenAI API Key: Get your key from [OpenAI's API Keys page](https://platform.openai.com/api-keys)
            2. X (Twitter) API Credentials:
                * Go to [X Developer Portal](https://developer.twitter.com/en/portal/dashboard)
                * Create a new project/app
                * Enable OAuth 1.0a in app settings
                * Generate API Key, API Key Secret, Access Token, and Access Token Secret
            """)
            
            print("\nInitializing credential textboxes...")
            
            def load_initial_values():
                print("\nLoading initial values...")
                for key, value in initial_values.items():
                    print(f"{key}: {'[SET]' if value else '[EMPTY]'} (length: {len(value) if value else 0})")
                return [
                    gr.update(value=initial_values['openai_key']),
                    gr.update(value=initial_values['twitter_api_key']),
                    gr.update(value=initial_values['twitter_api_secret']),
                    gr.update(value=initial_values['twitter_access_token']),
                    gr.update(value=initial_values['twitter_access_token_secret'])
                ]
            with gr.Row():
                telegram_bot_token = gr.Textbox(
                    label="Telegram Bot Token",
                    type="password",
                    show_label=True,
                    container=True,
                    scale=1,
                    interactive=True,
                    value=bot.credentials.get('telegram_bot_token', '')
                )

                telegram_chat_id = gr.Textbox(
                    label="Telegram Chat ID",
                    type="text",
                    show_label=True,
                    container=True,
                    scale=1,
                    interactive=True,
                    value=bot.credentials.get('telegram_chat_id', '')
                )
            
            with gr.Row():
                openai_key = gr.Textbox(
                    label="OpenAI API Key",
                    type="password",
                    show_label=True,
                    container=True,
                    scale=1,
                    interactive=True,
                    value=initial_values['openai_key']
                )
                print(f"OpenAI Key textbox initialized")
            
            with gr.Row():
                twitter_api_key = gr.Textbox(
                    label="Twitter API Key",
                    type="password",
                    show_label=True,
                    container=True,
                    scale=1,
                    interactive=True,
                    value=initial_values['twitter_api_key']
                )
                print(f"Twitter API Key textbox initialized")
                
                twitter_api_secret = gr.Textbox(
                    label="Twitter API Secret",
                    type="password",
                    show_label=True,
                    container=True,
                    scale=1,
                    interactive=True,
                    value=initial_values['twitter_api_secret']
                )
                print(f"Twitter API Secret textbox initialized")
            
            with gr.Row():
                twitter_access_token = gr.Textbox(
                    label="Twitter Access Token",
                    type="password",
                    show_label=True,
                    container=True,
                    scale=1,
                    interactive=True,
                    value=initial_values['twitter_access_token']
                )
                print(f"Twitter Access Token textbox initialized")
                
                twitter_access_token_secret = gr.Textbox(
                    label="Twitter Access Token Secret",
                    type="password",
                    show_label=True,
                    container=True,
                    scale=1,
                    interactive=True,
                    value=initial_values['twitter_access_token_secret']
                )
                print(f"Twitter Access Token Secret textbox initialized")
            with gr.Row():
                bearer_token = gr.Textbox(
                    label="Twitter Bearer Token",
                    type="password",
                    show_label=True,
                    container=True,
                    scale=1,
                    interactive=True,
                    value=bot.credentials.get('bearer_token', '')
                )

            def save_creds(key, api_key, api_secret, access_token, access_secret, telegram_token, telegram_chat, bearer_token):

                print("\nSaving credentials...")
                print(f"OpenAI Key length: {len(key) if key else 0}")
                print(f"API Key length: {len(api_key) if api_key else 0}")
                print(f"API Secret length: {len(api_secret) if api_secret else 0}")
                print(f"Access Token length: {len(access_token) if access_token else 0}")
                print(f"Access Token Secret length: {len(access_secret) if access_secret else 0}")
                
                credentials = {
                    'openai_key': key,
                    'twitter_api_key': api_key,
                    'twitter_api_secret': api_secret,
                    'twitter_access_token': access_token,
                    'twitter_access_token_secret': access_secret,
                    'telegram_bot_token': telegram_token,
                    'telegram_chat_id': telegram_chat,
                    'bearer_token': bearer_token
                }
                
                if bot.save_credentials(credentials):
                    print("Credentials saved successfully")
                    print(f"New credentials: {list(bot.credentials.keys())}")
                    # Update initial values for future loads
                    initial_values.update(credentials)
                    return ("Credentials saved successfully", 
                        gr.update(value=key),
                        gr.update(value=api_key),
                        gr.update(value=api_secret),
                        gr.update(value=access_token),
                        gr.update(value=access_secret),
                        gr.update(value=telegram_token),
                        gr.update(value=telegram_chat),
                        gr.update(value=bearer_token))

                else:
                    print("Failed to save credentials")
                    return ("Failed to save credentials",
                        gr.update(value=bot.credentials.get('openai_key', '')),
                        gr.update(value=bot.credentials.get('twitter_api_key', '')),
                        gr.update(value=bot.credentials.get('twitter_api_secret', '')),
                        gr.update(value=bot.credentials.get('twitter_access_token', '')),
                        gr.update(value=bot.credentials.get('twitter_access_token_secret', '')),
                        gr.update(value=bot.credentials.get('telegram_bot_token', '')),
                        gr.update(value=bot.credentials.get('telegram_chat_id', '')),
                        gr.update(value=bot.credentials.get('bearer_token', '')))
            
            with gr.Row():
                save_button = gr.Button("Save Credentials", variant="primary")
                save_status = gr.Textbox(label="Status", interactive=False)
            
            save_button.click(
            save_creds,
            inputs=[
                openai_key, twitter_api_key, twitter_api_secret,
                twitter_access_token, twitter_access_token_secret,
                telegram_bot_token, telegram_chat_id, bearer_token
            ],
            outputs=[
                save_status, openai_key, twitter_api_key, twitter_api_secret,
                twitter_access_token, twitter_access_token_secret,
                telegram_bot_token, telegram_chat_id, bearer_token
            ]
        )
        print("\nInitializing character management components...")
        with gr.Accordion("👤 Character Management", open=True):
            gr.Markdown("Create and manage your AI characters")

            # Get list of characters and set default (moved to top)
            char_choices = list(bot.characters.keys())
            default_char = None
            
            with gr.Row():
                control_character = gr.Dropdown(
                    label="Character",
                    choices=char_choices,
                    value=default_char,
                    interactive=True,
                    show_label=True,
                    container=True,
                    scale=1,
                    allow_custom_value=False # Should not allow custom values here
                )
                character_select_button = gr.Button("Select Character", variant="primary")
            
            with gr.Row():
                delete_char_dropdown = gr.Dropdown(
                    label="Select character to delete",
                    choices=char_choices,
                    value=default_char,
                    interactive=True,
                    show_label=True,
                    container=True,
                    scale=1,
                    allow_custom_value=True
                )
                delete_button = gr.Button("Delete Character", variant="secondary")

            with gr.Tabs():
                with gr.TabItem("Manual Creation"):
                    with gr.Row():
                        character_name = gr.Textbox(
                            label="Character Name",
                            show_label=True,
                            container=True,
                            scale=1,
                            interactive=True,
                            placeholder="Enter character name..."
                        )
                    
                    with gr.Row():
                        character_prompt = gr.Textbox(
                            label="Character System Prompt",
                            lines=5,
                            placeholder="Enter the system prompt that defines this character's personality...",
                            show_label=True,
                            container=True,
                            scale=1,
                            interactive=True,
                            value="",
                        )
                    
                    with gr.Row():
                        model_dropdown = gr.Dropdown(
                            label="Select Model",
                            choices=list(OPENAI_MODELS.keys()),
                            value=next((k for k, v in OPENAI_MODELS.items() 
                                    if bot.characters and v['name'] == next(iter(bot.characters.values()))['model']), 
                                    "gpt-3.5-turbo (Most affordable)"),
                            show_label=True,
                            container=True,
                            scale=1,
                            interactive=True
                        )
                        print(f"Model dropdown initialized with choices: {list(OPENAI_MODELS.keys())}")

                with gr.TabItem("Import from Assistant"):
                    with gr.Row():
                        assistant_char_name = gr.Textbox(
                            label="Character Name",
                            show_label=True,
                            container=True,
                            scale=1,
                            interactive=True,
                            placeholder="Enter character name..."
                        )
                        
                        assistant_id = gr.Textbox(
                            label="OpenAI Assistant ID",
                            show_label=True,
                            container=True,
                            scale=1,
                            interactive=True,
                            placeholder="asst_..."
                        )
                    
                    with gr.Row():
                        import_assistant_btn = gr.Button("Import Assistant", variant="primary")
                        import_status = gr.Textbox(label="Import Status", interactive=False)
                    
                    def import_assistant(name, asst_id):
                        if not name or not asst_id:
                            return ("Name and Assistant ID are required",
                                   list(bot.characters.keys()),
                                   None,
                                   list(bot.characters.keys()))
                        
                        success, message = bot.save_character_from_assistant(name, asst_id)
                        if success:
                            new_choices = list(bot.characters.keys())
                            return (message,
                                   gr.update(choices=new_choices, value=name),  # delete_char_dropdown
                                   name,         # character_name
                                   gr.update(choices=new_choices, value=name))  # control_character
                        else:
                            return (message,
                                   list(bot.characters.keys()),
                                   None,
                                   list(bot.characters.keys()))
                    
                    import_assistant_btn.click(
                        import_assistant,
                        inputs=[assistant_char_name, assistant_id],
                        outputs=[import_status, delete_char_dropdown, character_name, 
                                control_character]
                    )

            def delete_character(char_name):
                print(f"\nDeleting character: {char_name}")
                if not char_name:
                    return ("Please select a character to delete",
                           list(bot.characters.keys()),
                           "",
                           None,
                           list(bot.characters.keys()))
                print(f"Current characters before deletion: {list(bot.characters.keys())}")

                characters = bot.characters.copy()
                if char_name in characters:
                    del characters[char_name]
                    if bot.save_characters(characters):
                        print(f"Character deleted successfully. Remaining characters: {list(bot.characters.keys())}")
                        new_choices = list(bot.characters.keys())
                        return ("Character deleted successfully",
                               gr.update(choices=new_choices, value=None),  # delete_char_dropdown
                               "",
                               None,         # character_name
                               gr.update(choices=new_choices, value=None))  # control_character
                else: 
                    print(f"Character '{char_name}' not found in characters list.")
                
                print("Failed to delete character")
                return ("Failed to delete character",
                       list(bot.characters.keys()),
                       "",
                       None,
                       list(bot.characters.keys()))
            
            def save_character(name, prompt, model_name):
                print(f"\nSaving character: {name}")
                print(f"Prompt length: {len(prompt) if prompt else 0}")
                print(f"Selected model: {model_name}")
                
                if not name or not prompt:
                    print("Error: Name and prompt are required")
                    return ("Name and prompt are required", [], None, [], None)
                
                characters = bot.characters.copy()
                characters[name] = {
                    'prompt': prompt,
                    'model': OPENAI_MODELS[model_name]['name']
                }
                
                if bot.save_characters(characters):
                    print(f"Character saved successfully. Characters: {list(bot.characters.keys())}")
                    # Update all character dropdowns
                    new_choices = list(bot.characters.keys())
                    return ("Character saved successfully", 
                           gr.update(choices=new_choices),  # delete_char_dropdown
                           name,        # character_name
                           gr.update(choices=new_choices),  # control_character
                           name)         # control_character value
                else:
                    print("Failed to save character")
                    return ("Failed to save character",
                           list(bot.characters.keys()),
                           None,
                           list(bot.characters.keys()),
                           None)
            
            with gr.Row():
                save_char_button = gr.Button("Add Character", variant="primary")
                save_char_status = gr.Textbox(label="Status", interactive=False)

                        # Connect character management event handlers
            save_char_button.click(
                save_character,
                inputs=[character_name, character_prompt, model_dropdown],
                outputs=[save_char_status, delete_char_dropdown, character_name, 
                        control_character]
            )

            delete_char_dropdown.change(
                bot.load_character_prompt,
                inputs=[delete_char_dropdown],
                outputs=[character_prompt]
            ) 

            # Connect delete button to handler
            delete_button.click(
                delete_character,
                inputs=[delete_char_dropdown],
                outputs=[save_char_status, delete_char_dropdown, character_name,
                        control_character] # <-- And these outputs
            )    
         # Control Center section
        with gr.Accordion("🎮 Control Center", open=True):
            gr.Markdown("Generate and post tweets using your AI characters")
            
            with gr.Row():

                # Add default handling for empty characters dictionary
                new_choices = list(bot.characters.keys())
                default_char = next(iter(bot.characters.keys())) if char_choices else None
                character_dropdown = gr.Dropdown(
                    choices=new_choices,
                    value=default_char,
                    label="Select Character"
                )
                subject_dropdown = gr.Dropdown(choices=["crypto", "ai"], value="crypto", label="Select Subject")
            
            with gr.Row():
                use_news = gr.Checkbox(value=True, label="Use News Feed", interactive=True)
                use_memes = gr.Checkbox(value=bot.use_memes, label="Use Memes", interactive=True)
                meme_frequency = gr.Number(value=bot.meme_frequency, label="Post meme every X tweets", minimum=1, maximum=100, step=1)
            
            current_topic = gr.Textbox(
                label="Current Topic/Story",
                lines=3,
                interactive=True

            )

                                # --- Subject / content controls ---
                subject_dropdown = gr.Dropdown(
                    choices=[("crypto", "crypto"), ("ai", "ai"), ("tech", "tech"), ("🎲 Surprise me (All)", "__surprise_all__")],
                    value="crypto",
                    label="Select Subject",
                    interactive=True
                )

                with gr.Row():
                    use_news = gr.Checkbox(value=True, label="Use News Feed", interactive=True)
                    use_memes = gr.Checkbox(value=bot.use_memes, label="Use Memes", interactive=True)
                    meme_frequency = gr.Number(value=bot.meme_frequency, label="Post meme every X tweets", minimum=1, maximum=100, step=1)

                current_topic = gr.Textbox(
                    label="Current Topic/Story",
                    lines=3,
                    interactive=True
                )

                with gr.Row():
                    new_story_btn = gr.Button("New Story")
                    tweet_btn = gr.Button("Post Single Tweet")

                tweet_status = gr.Textbox(label="Tweet Status", interactive=False)

                scheduler_enabled = gr.Checkbox(label="Enable Scheduler", value=False)
                scheduler_status = gr.Markdown("Scheduler: NOT RUNNING")

                # ---------- Helpers ----------
                import random

                def get_story_dispatch(subject):
                    if subject == "__surprise_all__":
                        # Try subjects in random order; first successful story wins
                        subjects = list(RSS_FEEDS.keys())  # e.g., ["crypto","ai","tech"]
                        random.shuffle(subjects)
                        for s in subjects:
                            story = bot.get_new_story(s)
                            if story:
                                return f"{story['title']}\n\n{story['preview']}\n\nRead more: {story['url']} (source: {s})"
                        return "No items found right now. Try again in a moment."
                    # Normal per-subject path
                    story = bot.get_new_story(subject)
                    if story:
                        return f"{story['title']}\n\n{story['preview']}\n\nRead more: {story['url']}"
                    return f"No items found for '{subject}' right now."

                # IMPORTANT: Do NOT auto-fetch on selection.
                # Just update the bot's subject so the scheduler uses it later.
                def _update_subject(subject):
                    bot.subject = subject
                    return gr.update()  # no UI change -> no network calls

                # Wire subject change ONLY to update the selected subject for the scheduler
                subject_dropdown.change(_update_subject, inputs=[subject_dropdown], outputs=[])

                # Button wiring (manual fetch only when you click New Story)
                new_story_btn.click(get_story_dispatch, inputs=[subject_dropdown], outputs=[current_topic])

                def send_tweet(character, topic):
                    success = bot.send_tweet(character, topic)
                    return "Tweet sent successfully!" if success else "Failed to send tweet. Please try again."

                tweet_btn.click(send_tweet, inputs=[character_dropdown, current_topic], outputs=[tweet_status])

            def toggle_scheduler(enabled, character, subject):
                if not character:
                    return "Please select a character first", "Scheduler: NOT RUNNING", current_topic.value
                    
                if enabled:
                    bot.scheduler_running = True
                    bot.scheduler_character = character
                    bot.scheduler_subject = subject

                    # If memes are enabled, start with a meme tweet
                    if bot.use_memes:
                        tweet_text, meme_path = bot.get_random_meme(character)
                        if tweet_text and meme_path:
                            if bot.send_tweet_with_media(tweet_text, meme_path):
                                # Reset meme counter after successful meme
                                bot.meme_counter = 0
                                
                                # Queue up first news story for next tweet
                                new_story = bot.get_new_story(subject)
                                if new_story:
                                    story_text = f"{new_story['title']}\n\n{new_story['preview']}\n\nRead more: {new_story['url']}"
                                    bot.tweet_queue.put((character, story_text, subject))
                                
                                # Start the worker thread
                                threading.Thread(target=bot.scheduler_worker, daemon=True).start()
                                return f"Scheduler started with meme tweet: {tweet_text}", "Scheduler: RUNNING", current_topic.value
                            
                        # Only proceed to news if memes are disabled or meme tweet completely failed
                        print("Meme tweet failed, falling back to news")
                    
                    # If no memes or meme tweet failed, start with news
                    new_story = bot.get_new_story(subject)
                    if not new_story:
                        bot.scheduler_running = False
                        return "Failed to fetch news story", "Scheduler: NOT RUNNING", current_topic.value
                        
                    story_text = f"{new_story['title']}\n\n{new_story['preview']}\n\nRead more: {new_story['url']}"
                    
                    # Send first tweet
                    tweet_text = bot.generate_tweet(character, story_text)
                    if tweet_text and bot.send_tweet(tweet_text):
                        # Queue up next story before starting worker
                        next_story = bot.get_new_story(subject)
                        if next_story:
                            # ✅ Fixed: use next_story['preview'] here
                            next_story_text = f"{next_story['title']}\n\n{next_story['preview']}\n\nRead more: {next_story['url']}"
                            bot.tweet_queue.put((character, next_story_text, subject))
                        
                        # Start the worker thread
                        threading.Thread(target=bot.scheduler_worker, daemon=True).start()
                        return f"Scheduler started and first tweet sent: {tweet_text}", "Scheduler: RUNNING", story_text
                    else:
                        bot.scheduler_running = False
                        return "Failed to send first tweet", "Scheduler: NOT RUNNING", current_topic.value
                else:
                    bot.scheduler_running = False
                    return "Scheduler stopped", "Scheduler: NOT RUNNING", current_topic.value

            scheduler_enabled.change(
                toggle_scheduler,
                inputs=[scheduler_enabled, character_dropdown, subject_dropdown],
                outputs=[tweet_status, scheduler_status, current_topic]
            )

                        
            def manual_tweet(character, topic):
                if not character:
                    return "Please select a character first"
                if not topic:
                    return "Please enter a topic or get a news story first"
                    
                tweet_text = bot.generate_tweet(character, topic)
                if tweet_text:
                    if bot.send_tweet(tweet_text):
                        if use_news.value:
                            new_story = bot.get_new_story(subject_dropdown.value)
                            if new_story:
                                current_topic.value = f"{new_story['title']}\n\n{new_story['preview']}\n\nRead more: {new_story['url']}"
                        return f"Tweet sent: {tweet_text}"
                    else:
                        return "Failed to send tweet. Please check your credentials."
                return "Failed to generate tweet. Please try again."
            
            tweet_btn.click(
                manual_tweet,
                inputs=[character_dropdown, current_topic],
                outputs=[tweet_status]
            )
        
        # Feed Configuration section
        with gr.Accordion("📰 Feed Configuration", open=True):
            gr.Markdown("Configure which RSS feeds to use for each subject")

            # --- Subject picker now includes whatever is in RSS_FEEDS (e.g., crypto, ai, tech) ---
            with gr.Row():
                feed_subject = gr.Dropdown(
                    label="Subject",
                    choices=list(RSS_FEEDS.keys()),
                    value="crypto",
                    interactive=True,
                    show_label=True,
                    container=True,
                    scale=1
                )

            # --- Helpers to refresh the checkbox groups for the selected subject ---
            def update_feed_checkboxes(subject):
                print(f"\nUpdating feed checkboxes for subject: {subject}")
                feed_config = bot.feed_config.get(subject, {})
                primary_feeds = RSS_FEEDS[subject]["primary"]
                secondary_feeds = RSS_FEEDS[subject]["secondary"]

                primary_choices = [f"{feed['name']} ({feed['url']})" for feed in primary_feeds]
                primary_values = [feed_config.get("primary", {}).get(feed["url"], True) for feed in primary_feeds]
                secondary_choices = [f"{feed['name']} ({feed['url']})" for feed in secondary_feeds]
                secondary_values = [feed_config.get("secondary", {}).get(feed["url"], True) for feed in secondary_feeds]

                print(f"Primary feeds: {len(primary_choices)} choices, {len(primary_values)} values")
                print(f"Secondary feeds: {len(secondary_choices)} choices, {len(secondary_values)} values")

                return [
                    gr.update(choices=primary_choices, value=[choice for i, choice in enumerate(primary_choices) if primary_values[i]]),
                    gr.update(choices=secondary_choices, value=[choice for i, choice in enumerate(secondary_choices) if secondary_values[i]])
                ]

            with gr.Column():
                gr.Markdown("### Primary Sources")
                primary_feeds = gr.CheckboxGroup(
                    label="Primary Sources",
                    choices=[f"{feed['name']} ({feed['url']})" for feed in RSS_FEEDS["crypto"]["primary"]],
                    value=[f"{feed['name']} ({feed['url']})" for feed in RSS_FEEDS["crypto"]["primary"]],
                    interactive=True
                )

                gr.Markdown("### Secondary Sources")
                secondary_feeds = gr.CheckboxGroup(
                    label="Secondary Sources",
                    choices=[f"{feed['name']} ({feed['url']})" for feed in RSS_FEEDS["crypto"]["secondary"]],
                    value=[f"{feed['name']} ({feed['url']})" for feed in RSS_FEEDS["crypto"]["secondary"]],
                    interactive=True
                )

            with gr.Row():
                save_feeds_btn = gr.Button("Save Feed Configuration", variant="primary")
                # New: random-any-category button
                surprise_all_btn = gr.Button("🎲 Surprise me (All Feeds)")
                save_feeds_status = gr.Textbox(label="Status", interactive=False)

            # Wire subject dropdown to checkbox refresh
            feed_subject.change(
                update_feed_checkboxes,
                inputs=[feed_subject],
                outputs=[primary_feeds, secondary_feeds]
            )

            # Save config
            save_feeds_btn.click(
                save_feed_selection,
                inputs=[feed_subject, primary_feeds, secondary_feeds],
                outputs=[save_feeds_status]
            )

            # --- Random across ALL feeds helper ---
            def get_random_story_all():
                # Try subjects in random order; first successful story wins
                subjects = list(RSS_FEEDS.keys())
                random.shuffle(subjects)
                for subj in subjects:
                    story = bot.get_new_story(subj)  # respects per-subject config inside your bot
                    if story:
                        return f"{story['title']}\n\n{story['preview']}\n\nRead more: {story['url']} (source: {subj})"
                return "No items found right now. Try again in a moment."

            # Initialize feed checkboxes for default subject
            feed_subject.value = "crypto"
            update_feed_checkboxes("crypto")

        # Simple helpers that already existed
        def get_story(subject):
            story = bot.get_new_story(subject)
            if story:
                return f"{story['title']}\n\n{story['preview']}\n\nRead more: {story['url']}"
            return "Failed to fetch new story. Please try again."

        def send_tweet(character, topic):
            success = bot.send_tweet(character, topic)
            return "Tweet sent successfully!" if success else "Failed to send tweet. Please try again."

        # Connect button handlers
        new_story_btn.click(get_story, inputs=[subject_dropdown], outputs=[current_topic])
        tweet_btn.click(send_tweet, inputs=[character_dropdown, current_topic], outputs=[tweet_status])

        # NEW: connect the Surprise me (All Feeds) button to fill current_topic
        surprise_all_btn.click(lambda: get_random_story_all(), outputs=[current_topic])

        # Connect checkbox handlers
        def update_news_feed(value):
            bot.use_news = value
            return value

        def update_memes(value):
            bot.use_memes = value
            return value

        def update_meme_frequency(value):
            bot.meme_frequency = int(value) if value else 5
            return value

        use_news.change(update_news_feed, inputs=[use_news], outputs=[use_news])
        use_memes.change(update_memes, inputs=[use_memes], outputs=[use_memes])
        meme_frequency.change(update_meme_frequency, inputs=[meme_frequency], outputs=[meme_frequency])

        return interface

def start_bot():
    bot.subject = subject_dropdown.value
    bot.character_name = character_dropdown.value
    bot.tweet_interval = tweet_interval.value
    bot.story_age_hours = story_age.value
    bot.use_news = use_news.value
    bot.use_memes = use_memes.value
    bot.meme_frequency = meme_frequency.value
    
    if not bot.scheduler_running:
        bot.start_scheduler()
        
    return {
        status: update_status(),
        next_tweet: update_next_tweet(),
        last_tweet: update_last_tweet()
    }
bot = TwitterBot()
def fetch_prompt_from_github(repo_url="https://raw.githubusercontent.com/Mork-Zuckerbarge/prime-directive/main/directive"):
    try:
        response = requests.get(repo_url)
        response.raise_for_status()
        print("✅ Prompt fetched from GitHub successfully.")
        return response.text.strip()
    except Exception as e:
        print(f"❌ Failed to fetch prompt from GitHub: {e}")
        return None

# Initialize bot
bot = TwitterBot()

# Fetch Mork's directive from GitHub
prompt_text = fetch_prompt_from_github()
if prompt_text:
    bot.save_characters({
        "mork zuckerbarge": {
            "prompt": prompt_text,
            "model": "gpt-4o"
        }
    })
    print("✅ Mork has been rewritten using GitHub prompt.")
else:
    fallback_prompt = """You are Mork Zuckerbarge, the CEO of BETA. You love literature and art...
    [insert full original prompt here]"""
    bot.save_characters({
        "mork zuckerbarge": {
            "prompt": fallback_prompt.strip(),
            "model": "gpt-4o"
        }
    })
    print("⚠️ Using fallback prompt instead.")


if __name__ == "__main__":
    interface = create_ui()
    
    # Schedule Mork's haunting reply checker
    schedule.every().day.at("10:00").do(bot.monitor_and_reply_to_mentions)
    threading.Thread(target=bot.scheduler_worker, daemon=True).start()

    print("🧠 Scheduler set. Launching Gradio...")

    # Run Gradio in a separate thread so we can run scheduler too
    def launch_gradio():
        interface.launch()

    threading.Thread(target=launch_gradio, daemon=True).start()

    # Run the scheduler in the CMD loop
    while True:
        schedule.run_pending()
        time.sleep(1)
