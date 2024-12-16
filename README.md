# News Tweet Agent

An automated Twitter bot that posts daily news updates about any topic. The bot fetches the latest news using SERP API, summarizes it using OpenAI's GPT-3.5, and posts it as a Twitter thread.

## Features

- Fetches latest news on any topic using SERP API
- Summarizes news articles using OpenAI GPT-3.5
- Posts daily Twitter threads
- Runs on Google Cloud Run with automated scheduling

## Prerequisites

- Python 3.9+
- Docker Desktop
- Google Cloud SDK
- Twitter Developer Account
- OpenAI API Key
- SERP API Key

## Obtaining Required Credentials

### 1. Twitter Developer Account Setup
1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Sign up for a developer account
3. Create a new Project and App
4. Under "User authentication settings":
   - Enable OAuth 1.0a
   - Set App permissions to "Read and write"
   - Set Type of App to "Web App"
5. Generate the following credentials:
   - API Key (Consumer Key)
   - API Key Secret (Consumer Secret)
   - Access Token
   - Access Token Secret
6. Generate Bearer Token from your app settings

### 2. OpenAI API Key
1. Visit [OpenAI API](https://platform.openai.com/signup)
2. Create an account or sign in
3. Go to API settings
4. Create a new API key
5. Save the key securely

### 3. SERP API Key
1. Go to [SERP API](https://serpapi.com/)
2. Sign up for an account
3. Navigate to your dashboard
4. Copy your API key

## Local Setup

1. Clone the repository and set up environment:
```bash
# Create and edit .env file with your credentials
cp .env.example .env
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your .env file:
```env
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_CONSUMER_KEY=your_consumer_key
TWITTER_CONSUMER_SECRET=your_consumer_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
SERP_API_KEY=your_serp_api_key
OPENAI_API_KEY=your_openai_api_key
```

4. Run locally:
```bash
python main.py
```

## Google Cloud Deployment

1. Install and Initialize Google Cloud SDK:
```bash
# Install Google Cloud SDK from: https://cloud.google.com/sdk/docs/install
gcloud auth login
gcloud config set project PROJECT_ID
```

2. Enable Required APIs:
```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com
```

3. Create Secrets in Google Cloud Secret Manager:
```bash
# Create each required secret
gcloud secrets create TWITTER_BEARER_TOKEN --data-file=-
gcloud secrets create TWITTER_CONSUMER_KEY --data-file=-
gcloud secrets create TWITTER_CONSUMER_SECRET --data-file=-
gcloud secrets create TWITTER_ACCESS_TOKEN --data-file=-
gcloud secrets create TWITTER_ACCESS_TOKEN_SECRET --data-file=-
gcloud secrets create SERP_API_KEY --data-file=-
gcloud secrets create OPENAI_API_KEY --data-file=-
```

4. Grant Secret Access to Service Account:
```bash
# Replace PROJECT_NUMBER with your project number
PROJECT_NUMBER=your-project-number
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

5. Deploy to Cloud Run:
```bash
gcloud run deploy ai-news-bot \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets="TWITTER_BEARER_TOKEN=TWITTER_BEARER_TOKEN:latest,TWITTER_CONSUMER_KEY=TWITTER_CONSUMER_KEY:latest,TWITTER_CONSUMER_SECRET=TWITTER_CONSUMER_SECRET:latest,TWITTER_ACCESS_TOKEN=TWITTER_ACCESS_TOKEN:latest,TWITTER_ACCESS_TOKEN_SECRET=TWITTER_ACCESS_TOKEN_SECRET:latest,SERP_API_KEY=SERP_API_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest"
```

6. Set up Cloud Scheduler:
```bash
# Create a scheduler job to run daily at 12:00 PM
gcloud scheduler jobs create http ai-news-daily \
  --location=us-central1 \
  --schedule="0 12 * * *" \
  --uri="[YOUR CLOUD RUN URL]" \
  --http-method=POST \
  --time-zone="America/New_York"
```

## Customizing Your News Feed

To change the topic of news you want to tweet about, modify the `search_query` parameter when initializing the TweetAgent:

```python
bot = TweetAgent(search_query="your topic here")
```

Examples:
- Technology news
- Sports updates
- Finance news
- Climate change news
- Entertainment news

## Project Structure

```
.
├── Dockerfile           # Container configuration
├── main.py             # Flask application entry point
├── tweet_agent.py      # Core bot functionality
├── requirements.txt    # Python dependencies
└── .env               # Local environment variables
```

## Monitoring and Troubleshooting

### Common Issues and Solutions

1. **Twitter API Authentication Issues**
   - Verify all Twitter credentials are correct
   - Check if your Twitter Developer Account is active
   - Ensure your app has proper permissions enabled

2. **SERP API Issues**
   - Verify your API key is active
   - Check your daily quota limits
   - Ensure your search query is properly formatted

3. **OpenAI API Issues**
   - Verify your API key is valid
   - Check your usage limits
   - Monitor your billing status

### Viewing Logs

In Google Cloud Console:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=news-tweet-bot"
```

## Rate Limits

- Twitter API: 300 tweets per 3 hours
- SERP API: Depends on your plan
- OpenAI API: Varies by subscription

## License

MIT

## Support

For issues and feature requests, please open an issue on GitHub.