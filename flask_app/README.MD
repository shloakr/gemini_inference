# Happenstance Message Classification API

Happenstance is an intelligent assistant designed to determine whether a given message is a request or not. This Flask-based API leverages Google's Generative AI (Gemini model) to classify messages, with specialized handling for LinkedIn-related content. To enhance performance and reduce redundant API calls, Redis caching is integrated into the system.

## Features

- **Message Classification**: Determines if a message is a request based on predefined criteria.
- **LinkedIn-Specific Handling**: Special classification logic for messages mentioning LinkedIn.
- **Caching with Redis**: Improves performance by caching classification results to avoid redundant API calls.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python 3.7+** installed on your machine.
- **Redis Server** installed and running.
- **Google Generative AI API Key**.

## Installation

1. **Satrt the Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate 
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Set environment variables**
```bash
GEMINI_API_KEY=GEMINI_AI_API_KEY
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password_if_any
```

## Running the Application
1. **Set up Redis Cache**
```bash
brew install redis
brew services start redis
```
2. **Run the Application**
```bash
python app.py
```

## Test the API
```bash
curl -X POST http://127.0.0.1:5003/classify \
     -H "Content-Type: application/json" \
     -d '{"message": "Is there someone at LinkedIn who worked in security?"}'
```

The API will return a JSON response containing the classification result and additional information.
Sample: 
```json
{
    "message": "Is there someone at LinkedIn who worked in security?",
    "classification": "Request",
    "classification_time": "0:00:02",
    "cached": false
}
```


