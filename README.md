Travel Planner AI Chatbot implementation consists of:

## Flask Backend (app.py):

* Implements the entire conversation flow from your diagram
* Uses a state machine approach to manage the conversation
* Integrates with OpenAI's API for natural language understanding


## Frontend (index.html):

* Clean, responsive UI with Bootstrap
* Real-time chat interface with typing indicators
* Visual state indicators to show the current conversation stage


## Product Database (travel_products.json):

* Sample travel product data with various attributes
* Used for matching user preferences with available options


## Documentation:

* Comprehensive project overview
* Technical implementation details
* Evaluation against the metrics you specified


## Deployment Files:

* Requirements file
* Dockerfile for containerization



## Key Features

1. State-Based Conversation Flow: Exactly matches your diagram with Start Conversation → User Input → Intent Clarity → Intent
Confirmation → Product Info Extraction → Product Recommendation → End Conversation
2. OpenAI Integration: Uses carefully crafted prompts to guide the AI through different conversation stages
3. Product Matching: Filters the travel products database based on user preferences
4. User Experience: Provides visual feedback with typing indicators and state display

## Running the Application

Set your OpenAI API key as an environment variable:
```
export OPENAI_API_KEY=your_api_key_here
```

Install the required packages:
```
pip install -r requirements.txt
```

Run the Flask application:
```
python app.py
```

Access the chatbot at http://localhost:5000

