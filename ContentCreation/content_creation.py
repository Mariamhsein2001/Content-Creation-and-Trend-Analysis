from flask import Flask, request, jsonify, Response
import ollama
from flask_cors import CORS
import requests
import time
app = Flask(__name__)
CORS(app)


# Endpoint for your Docker-hosted News API
NEWS_API_URL = "http://localhost:5001/api/news"  # Adjust the port as needed

def get_topics_sentiments(country, category):
    try:
        response = requests.get(NEWS_API_URL, params={"country": country, "category": category})
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print("Error fetching topics and sentiments:", e)
        return None


# Route to get brand info and content type from the user
@app.route('/api/gather_info', methods=['POST'])
def gather_info():
    data = request.json
    brand_info = data.get("brand_info")
    country = data.get("country")
    category = data.get("category")

    if not brand_info or not country or not category:
        return jsonify({"error": "Please provide brand information, country, and category."}), 400

    # Fetch topics and sentiments based on country and category
    topics_data = get_topics_sentiments(country, category)
    if not topics_data:
        return jsonify({"error": "Unable to fetch topics and sentiments."}), 500

    # Extract and format topics and sentiment analysis from topics_data
    topics = topics_data.get("topics", {})
    sentiment_analysis = topics_data.get("sentiment_analysis", {})

    # Transformation for trends and sentiments output
    trends = {f"Topic {i+1}": keywords for i, (topic, keywords) in enumerate(topics.items())}
    sentiments = {f"Topic {i+1}": details["sentiment"] for i, (topic, details) in enumerate(sentiment_analysis.items())}

    response = {
        "message": f"Brand info received: {brand_info}. Ready to generate content.",
        "topics": topics,
        "sentiments": sentiments
    }
    return jsonify(response)

# Stream generator for content generation
def generate_content_stream(prompt):
    try:
        # Make a streaming request to the ollama API
        response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}], stream=True)
        
        # Simulate typing by breaking response text into small chunks
        chunk_size = 50  # Set a small chunk size for a "typing" effect
        for chunk in response:
            text = chunk['message']['content']
            for i in range(0, len(text), chunk_size):
                yield text[i:i + chunk_size]  # Yield each small chunk
                time.sleep(0.1)  # Add delay to simulate typing
    except KeyError:
        yield '{"error": "Unexpected response from content generation service."}'
    except Exception as e:
        yield f'{{"error": "{str(e)}"}}'

# Route for generating content with streaming response
@app.route('/api/generate_content', methods=['POST'])
def generate_content():
    data = request.json
    brand_info = data.get("brand_info")
    content_type = data.get("content_type")
    country = data.get("country")
    category = data.get("category")

    if not brand_info or not content_type or not country or not category:
        return jsonify({"error": "Please provide brand information, content type, country, and category."}), 400

    # Fetch topics and sentiments
    topics_data = get_topics_sentiments(country, category)
    if not topics_data:
        return jsonify({"error": "Unable to fetch topics and sentiments."}), 500

    # Extract topics and sentiments
    topics = {f"Topic {i+1}": keywords for i, (topic, keywords) in enumerate(topics_data.get("topics", {}).items())}
    sentiments = {f"Topic {i+1}": details['sentiment'] for i, (topic, details) in enumerate(topics_data.get("sentiment_analysis", {}).items())}

    # Construct the trends text for the prompt with sentiment
    trends_text = "\n".join([
        f"- {topic}: Keywords: {', '.join(keywords)} | Sentiment: {sentiments.get(topic, 'Neutral')}"
        for topic, keywords in topics.items()
    ])
    
    # Update the prompt to include sentiment information
    prompt = (
        f"Based on the following trending topics with associated sentiments:\n{trends_text}\n\n"
        f"Considering the brand identity described as: {brand_info}, "
        f"please create a unique and creative {content_type} for each topic that aligns with the sentiment.\n\n"
        f"Make sure to write in this format:\n"
        f"Topic '1' : [list of words in the trending topic 1 ] \n"
        f"Title of Content:\n"
        f"Content: \n"
        f"ONLY in case the content we are creating a social media post you should add visual description for each topic"
        f"why this content: like explain how it relates to the brand and trend for each topic \n"
        f"and same for the other topics.Stop when the content for the last topic is finished don't add anything else."
        f"don't include the word topic in the why this content "

    )

    # Return a streaming response using the generate_content_stream generator
    return Response(generate_content_stream(prompt), content_type='application/json')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
