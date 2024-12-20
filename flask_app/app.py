from flask import Flask, request, jsonify
import google.generativeai as genai
from datetime import timedelta
import time
import redis
import hashlib
import os

# Configure Generative AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None) 

try:
    redis_client = redis.StrictRedis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True 
    )
    # Test the connection
    redis_client.ping()
    print("Connected to Redis successfully!")
except redis.exceptions.ConnectionError as e:
    print(f"Redis connection error: {e}")
    redis_client = None  

app = Flask(__name__)

# Helper functions for Redis caching
def generate_cache_key(prefix, msg):
    """Generates a SHA256 hash as a cache key."""
    hash_object = hashlib.sha256(f"{prefix}:{msg}".encode())
    return hash_object.hexdigest()

def get_cached_response(key):
    """Retrieves a cached response from Redis."""
    if redis_client:
        return redis_client.get(key)
    return None

def set_cached_response(key, value, expiration=3600):
    """Sets a response in Redis cache with an expiration time (default: 1 hour)."""
    if redis_client:
        redis_client.set(key, value, ex=expiration)

# Define helper functions
def classify_msg_linkedin(msg):
    prompt = (
        f"""
        You are Happenstance, an assistant that determines whether a given message is a request or not.
        You work for Happenstance, which is not a general purpose chatbot. We help users find employees, connect with investors, and look for people based on a general topic, location, name of a company, etc.
        If we decide not to run a search, we should provide the user with helpful education about Happenstance.

        This message mentions LinkedIn, we don't have access to LinkedIn API yet. 
        We can't answer questions about LinkedIn Profile Data, Share Content, Search, Connection data, Retrieve Company Data on LinkedIn, etc
        However, be careful, the message may want to know about LinkedIn or people who have worked with LinkedIn.

        Evaluation criteria: for non-requests 
        - If it is not within the scope of our service; it is not about professional backgrounds, company affiliations, location, a job description/title or profession, or general topics
        - If it is inappropriate for the purpose of this chatbot
        - Social media posts that don't have a clear appropirate request
        - It asks you to search or use a LinkedIn feature—we don't have access to any LikedIn features yet

        Examples of LinkedIn non-requests:
        - Search LinkedIn Profile Data like name, location, or company
        - Share Content on my LinkedIn profile
        - Find Connections on linkedIn
        - Retrieve Company Data on LinkedIn
        - How many connections do I have?

        Evaluvation criteria for request:
        - A description or a statement about query is a request
        - It talks about/asks about employee connections, a specific background, company connections, job posting/title/description/profession, company name, potential customers, locations, connections, connecting with or needing people in general, needing a solution to a problem or needing help where we can add value, meeting/connecting with people for any appropriate reason, and general topics
        - If you can infer an appropriate request from the message, you can classify it as a request
        - If the message is long, but has a part that looks like a request, you can classify it as a request

        Examples of LinkedIn requests:
        - I met Alex Chen on LinkedIn, What is the name of the company that Alex works for?
        - Engineer at LinkedIn who worked in security?
        - Is there someone at LinkedIn who worked in security?

        Output:
        - If the message is a request, respond with: "Request"
        - If the message is not a request, respond with: "This is not a request because we don't have access to the LinkedIn API yet: [concise reason]"

        If the output is a not a request, output criteria:
        - Explain why the message is not a request
        - Always tell the user how they can use Happenstance correctly
        - Don't use any innapropriate language
        - Be very very consice and mature in your responses
        - If you get a salutation or feedback reply appropriately
        - Have a friendly and positive tone. 
        - Don't mention their message in your response
        - If their question is too vague/general, provide a more specific question

        **Scratchpad:**
        - Do I need to use LinkedIn to answer this question? If so, this is a non-request
        - Is the message asking me something about LinkedIn Profile Data, Sharing Content, Searching Connections, Retrieving Company Data on LinkedIn?
        - Is the message about someone who has worked with LinkedIn or has a connection with LinkedIn? If so, this is a request. 

        Message: "{msg}"
        """
    )
    response = model.generate_content(prompt)
    classification = response.text.strip()
    return classification

def format_time(elapsed_time):
    """Takes a time in seconds and returns a string hh:mm:ss"""
    elapsed_rounded = int(round(elapsed_time))
    return str(timedelta(seconds=elapsed_rounded))

def classify_msg(msg):
    prompt = (
        f"""
        You are Happenstance, an assistant that determines whether a given message is a request or not.
        You work for Happenstance, which is not a general purpose chatbot. We help users find employees, connect with investors, and look for people based on a general topic, location, name of a company, etc.
        If we decide not to run a search, we should provide the user with helpful education about Happenstance.

        Evaluvation criteria for not a request: 
        - If it is not within the scope of our service; it is not about professional backgrounds, company affiliations, location, a job description/title or profession, or general topics
        - If it is inappropriate for the purpose of this chatbot
        - Social media posts that don't have a clear appropirate request
        - If you can infer an appropriate request from the message, you can classify it as a request


        Evaluvation criteria for request:
        - A description or a statement about query is a request
        - It talks about/asks about employee connections, a specific background, company connections, company name, potential customers, locations, connections, connecting with or needing people in general, needing a solution to a problem or needing help where we can add value, meeting/connecting with people for any appropriate reason, and general topics
        - General messages are requests if they are appropriate and you can infer a request. 
        - If the message is long, but has a part that looks like a request, you can classify it as a request
        - A job posting is a request
        - A profession like doctor, astraunaut, lawyer, celebrity is a request
        - An issue faced by a usser is a request, they expect use to help solve it


        Output:
        - If the message is a request, respond with: "Request"
        - If the message is not a request, respond with: "This is not a request because: [concise reason]"

        If the output is a not a request, output criteria:
        - Explain why the message is not a request
        - Always tell the user how they can use Happenstance correctly
        - Don't use any innapropriate language
        - Be very very consice and mature in your responses
        - If you get a salutation or feedback reply appropriately
        - Have a friendly and positive tone. 
        - Don't mention their message in your response
        - If their question is too vague/general, provide a more specific question

        **Scratchpad:**
        - Can I decipher or infer a clear request in this message asking for information that I can provide?
        - Is the message about professional backgrounds, company affiliations, location, a job description/title or profession, or general topics?
        - Is the message inappropriate for the purpose of this chatbot? Does the request fit within our service?
        - Is the message a social media post that doesn't have a clear appropirate request?

        Message: "{msg}"
        """
    )
    response = model.generate_content(prompt)
    classification = response.text.strip()
    return classification


@app.route('/classify', methods=['POST'])
def classify_message():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'Invalid input, "message" key is required'}), 400

    msg = data['message']
    is_linkedin = "linkedin" in msg.lower()

    classification_start_time = time.time()

    # Generate a unique cache key based on message type and content
    prefix = 'linkedin' if is_linkedin else 'general'
    cache_key = generate_cache_key(prefix, msg)

    try:
        cached_classification = get_cached_response(cache_key)
        if cached_classification:
            classification = cached_classification
            cached = True
        else:
            classification = classify_msg_linkedin(msg) if is_linkedin else classify_msg(msg)
            set_cached_response(cache_key, classification)
            cached = False

        classification_time = time.time() - classification_start_time
        formatted_classification_time = str(timedelta(seconds=int(round(classification_time))))

    except Exception as e:
        return jsonify({'error': f'Classification failed: {str(e)}'}), 500

    # Return response
    return jsonify({
        'message': msg,
        'classification': classification,
        'classification_time': formatted_classification_time,
        'cached': cached 
    })

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
