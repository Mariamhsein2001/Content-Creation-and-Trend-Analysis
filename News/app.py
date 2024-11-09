from flask import Flask, request, jsonify, send_file
from newsapi import NewsApiClient
import nltk
import re
import os
import logging
import io
import base64
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation as LDA
from textblob import TextBlob
from dotenv import load_dotenv
from flask_cors import CORS
from wordcloud import WordCloud
from collections import Counter
import matplotlib.pyplot as plt
from nltk.tokenize import word_tokenize
from nltk import pos_tag

load_dotenv()
# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app and News API client
app = Flask(__name__)
CORS(app)
api_key = os.getenv('NEWS_API')
if not api_key:
    logging.error("API Key not found. Please set the NEWS_API environment variable.")
    raise ValueError("API Key not found. Please set the NEWS_API environment variable.")

api = NewsApiClient(api_key=api_key)

# Download NLTK resources
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('punkt_tab')
# Set up lemmatizer and stop words
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def fetch_trending_news(country, category):
    query = f"{category} in {country}"
    logging.info(f"Fetching news with query: {query}")

    try:
        output = api.get_everything(q=query, sort_by='relevancy', language='en')
        if 'articles' not in output:
            logging.error(f"Unexpected response structure: {output}")
            return []
        return output['articles']
    except Exception as e:
        logging.error(f"Error fetching news from API: {e}")
        return []

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = word_tokenize(text)
    
    # POS tagging
    pos_tags = pos_tag(tokens)
    
    # Stop word removal, lemmatization, and optional POS filtering
    tokens = [lemmatizer.lemmatize(word) for word, tag in pos_tags if word not in stop_words]
    
    # Optional: Filter tokens based on POS tags (e.g., keep only nouns and adjectives)
    # Example: Keep only nouns (NN, NNS, NNP, NNPS) and adjectives (JJ, JJS, JJR)
    allowed_pos_tags = {'NN', 'NNS', 'NNP', 'NNPS', 'JJ', 'JJS', 'JJR'}
    tokens = [word for word, tag in pos_tags if tag in allowed_pos_tags and word not in stop_words]
    
    return ' '.join(tokens)
def extract_keywords(documents, max_keywords=20):
    tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_features=max_keywords)
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
    feature_names = tfidf_vectorizer.get_feature_names_out()

    # Extract keywords for each document
    keywords = []
    for i in range(len(documents)):
        doc_keywords = [feature_names[index] for index in tfidf_matrix[i].nonzero()[1]]
        keywords.append(doc_keywords)

    # Flatten and count occurrences for word cloud
    all_keywords = [word for sublist in keywords for word in sublist]
    keyword_counts = Counter(all_keywords)

    return keywords, keyword_counts

def generate_wordcloud(keyword_counts):
    wordcloud = WordCloud(width=600, height=300, background_color='white').generate_from_frequencies(keyword_counts)
    
    # Save the wordcloud to a bytes buffer
    img_buffer = io.BytesIO()
    wordcloud.to_image().save(img_buffer, format='PNG')
    img_buffer.seek(0)

    # Convert to base64 for frontend display
    wordcloud_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    return wordcloud_base64


def topic_modeling(documents, num_topics=3, num_words=5):
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
    lda_model = LDA(n_components=num_topics, random_state=0)
    lda_model.fit(tfidf_matrix)
    feature_names = tfidf_vectorizer.get_feature_names_out()
    return {f"Topic {i + 1}": [feature_names[j] for j in topic.argsort()[:-num_words - 1:-1]] for i, topic in enumerate(lda_model.components_)}

def analyze_sentiment(documents, topics):
    topic_sentiments = {topic: [] for topic in topics}

    for doc in documents:
        for topic, keywords in topics.items():
            relevant_sentences = [sentence for sentence in doc.split('. ') if any(keyword in sentence for keyword in keywords)]
            topic_polarity = [TextBlob(sentence).sentiment.polarity for sentence in relevant_sentences]

            if topic_polarity:
                avg_sentiment = sum(topic_polarity) / len(topic_polarity)
                topic_sentiments[topic].append(avg_sentiment)

    results = {}
    sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for topic, sentiments in topic_sentiments.items():
        if sentiments:
            avg_sentiment = sum(sentiments) / len(sentiments)
            if avg_sentiment > 0:
                sentiment_type = "Positive"
            elif avg_sentiment < 0:
                sentiment_type = "Negative"
            else:
                sentiment_type = "Neutral"
            sentiment_counts[sentiment_type] += 1
            results[topic] = {"sentiment": sentiment_type, "average_polarity": avg_sentiment}
        else:
            results[topic] = {"sentiment": "No relevant mentions found."}

    return results, sentiment_counts

@app.route('/api/news', methods=['GET'])
def get_news():
    country = request.args.get('country')
    category = request.args.get('category')

    if not country or not category:
        return jsonify({"error": "Country and category are required parameters."}), 400

    articles = fetch_trending_news(country, category)
    documents = [f"{article['title']} {article['description']}" for article in articles]

    if not documents:
        return jsonify({"error": "No articles found for the given parameters."}), 404

    descriptions = [preprocess_text(doc) for doc in documents]
    keywords, keyword_counts = extract_keywords(descriptions, max_keywords=20)
    topics = topic_modeling(descriptions)  # Keep this function if you need topic modeling
    sentiment_results, sentiment_counts = analyze_sentiment(descriptions, topics)

    # Generate wordcloud image and prepare it for sending
    wordcloud_image_base64 = generate_wordcloud(keyword_counts)

    response = {
        "topics": topics,
        "sentiment_analysis": sentiment_results,
        "sentiment_counts": sentiment_counts,
        "wordcloud_image": wordcloud_image_base64
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
