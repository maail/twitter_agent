# main.py
import os
from flask import Flask, request, jsonify
from tweet_agent import TweetAgent

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def tweet_news():
    try:
        # Get search query from request parameters, default to "news"
        search_query = request.args.get('query', 'news')
        
        # Initialize and run the bot with environment variables
        print(f"Initializing TweetAgent with query: {search_query}")
        bot = TweetAgent(search_query=search_query)
        
        # Get news
        print("Fetching news...")
        stories = bot.get_news()
        
        if stories:
            # Create and send tweet thread
            tweets = bot.create_tweet_thread(stories)
            result = bot.send_thread(tweets)
            
            if result['success']:
                return jsonify({
                    'status': 'success',
                    'message': 'Tweet thread sent successfully',
                    'query': search_query,
                    'data': result
                }), 200
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to send tweets',
                    'query': search_query,
                    'data': result
                }), 400
        else:
            return jsonify({
                'status': 'error',
                'message': f'No news found for query: {search_query}',
                'query': search_query
            }), 400
            
    except Exception as e:
        print(f"Error in tweet_news: {str(e)}")  # Add explicit error logging
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}',
            'query': search_query if 'search_query' in locals() else 'undefined'
        }), 500

@app.route("/health", methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)