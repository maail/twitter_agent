import os
import json
import requests
import tweepy
import trafilatura
from trafilatura.settings import use_config
from openai import OpenAI
from datetime import datetime
import time
import openai

class TweetAgent:
    def __init__(self, search_query="artificial intelligence news"):
        """Initialize the Tweet Agent with required clients and configurations"""
        self.search_query = search_query
        # Initialize configurations
        self.setup_credentials()
        self.setup_clients()
        
        # Configure trafilatura
        self.trafilatura_config = use_config()
        self.trafilatura_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")
        
        # Twitter constants
        self.MAX_TWEET_LENGTH = 280
        self.URL_LENGTH = 23  # Twitter treats all URLs as 23 characters

    def setup_credentials(self):
        print(f"OpenAI version: {openai.__version__}")
        """Set up all required API credentials"""
        # These will be set by Cloud Run from secrets
        self.serp_api_key = os.environ.get('SERP_API_KEY')
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        # Print each environment variable status (without revealing the actual values)
        print("Environment Variables Status:")
        print(f"TWITTER_BEARER_TOKEN: {'✓' if os.environ.get('TWITTER_BEARER_TOKEN') else '✗'}")
        print(f"TWITTER_CONSUMER_KEY: {'✓' if os.environ.get('TWITTER_CONSUMER_KEY') else '✗'}")
        print(f"TWITTER_CONSUMER_SECRET: {'✓' if os.environ.get('TWITTER_CONSUMER_SECRET') else '✗'}")
        print(f"TWITTER_ACCESS_TOKEN: {'✓' if os.environ.get('TWITTER_ACCESS_TOKEN') else '✗'}")
        print(f"TWITTER_ACCESS_TOKEN_SECRET: {'✓' if os.environ.get('TWITTER_ACCESS_TOKEN_SECRET') else '✗'}")
        print(f"SERP_API_KEY: {'✓' if self.serp_api_key else '✗'}")
        print(f"OPENAI_API_KEY: {'✓' if self.openai_api_key else '✗'}")
        
        if not all([
            os.environ.get('TWITTER_BEARER_TOKEN'),
            os.environ.get('TWITTER_CONSUMER_KEY'),
            os.environ.get('TWITTER_CONSUMER_SECRET'),
            os.environ.get('TWITTER_ACCESS_TOKEN'),
            os.environ.get('TWITTER_ACCESS_TOKEN_SECRET'),
            self.serp_api_key,
            self.openai_api_key
        ]):
            raise ValueError("Missing required environment variables")
    
    def setup_clients(self):
        """Initialize API clients"""
        # Initialize Twitter client with v2 API
        self.client = tweepy.Client(
            bearer_token=os.environ.get('TWITTER_BEARER_TOKEN'),
            consumer_key=os.environ.get('TWITTER_CONSUMER_KEY'),
            consumer_secret=os.environ.get('TWITTER_CONSUMER_SECRET'),
            access_token=os.environ.get('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
        )
        
        # OpenAI client
        self.openai_client = OpenAI(
            api_key=self.openai_api_key
        )

    def get_news(self):
        """Fetch latest news using SERP API based on search query"""
        params = {
            "q": self.search_query,
            "location": "United States",
            "h1": "en",
            "gl": "us",
            "google_domain": "google.com",
            "api_key": self.serp_api_key,
        }

        try:
            response = requests.get("https://serpapi.com/search", params=params)
            parsed_data = json.loads(response.text)
            
            if parsed_data.get("top_stories"):
                return parsed_data["top_stories"][:3]  # Get top 3 stories
            return None
        except Exception as e:
            print(f"Error fetching news: {e}")
            return None

    def summarize_article(self, content):
        """Summarize article content using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for text summarization."},
                    {"role": "user", "content": f"Summarize this article in one very concise sentence (maximum 180 characters): {content}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error summarizing content: {e}")
            return None

    def truncate_text(self, text, max_length):
        """Truncate text to fit within Twitter's limits"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

    def create_tweet_thread(self, stories):
        """Create a tweet thread from the news stories"""
        tweets = []
        
        # First tweet in thread
        timestamp = datetime.now().strftime("%Y-%m-%d")
        topic = self.search_query.title()
        tweets.append(f"📰 Top {topic} News for {timestamp}\n\nA thread 🧵")
        
        for story in stories:
            # Download and extract article content
            downloaded = trafilatura.fetch_url(story['link'])
            content = trafilatura.extract(downloaded, config=self.trafilatura_config)
            
            if content:
                summary = self.summarize_article(content)
                if summary:
                    # Calculate available space for summary
                    available_length = self.MAX_TWEET_LENGTH - (self.URL_LENGTH + 10)
                    truncated_summary = self.truncate_text(summary, available_length)
                    
                    # Create tweet with summary and link
                    tweet = f"📰 {truncated_summary}\n{story['link']}"
                    tweets.append(tweet)
        
        # Add closing tweet
        tweets.append(f"📰 That's all for now! Stay tuned for more {topic} updates!")
        return tweets

    def send_tweet(self, tweet_text, reply_to_id=None):
        """Send a tweet using the Twitter API v2"""
        if not self.client:
            raise ValueError("Twitter API client not initialized properly.")
            
        try:
            if reply_to_id:
                tweet = self.client.create_tweet(text=tweet_text, in_reply_to_tweet_id=reply_to_id)
            else:
                tweet = self.client.create_tweet(text=tweet_text)
            
            return {
                'success': True,
                'tweet_id': tweet.data['id'],
                'text': tweet_text
            }
        except tweepy.errors.Forbidden as e:
            return {
                'success': False,
                'error': f"Forbidden error: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error: {str(e)}"
            }

    def send_thread(self, tweets):
        """Send a thread of tweets"""
        results = []
        previous_tweet_id = None
        
        for tweet in tweets:
            result = self.send_tweet(tweet, previous_tweet_id)
            
            if result['success']:
                results.append(result)
                previous_tweet_id = result['tweet_id']
                # Wait between tweets to avoid rate limits
                time.sleep(2)
            else:
                print(f"Failed to send tweet: {result['error']}")
                break
        
        return {
            'success': len(results) > 0,
            'thread': results
        }