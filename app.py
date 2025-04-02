from flask import Flask, render_template, request, jsonify, session
import os
from openai import OpenAI
import json
import re
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)


# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Sample travel products database (in a real app, this would be in a database)
with open('travel_products.json', 'r') as f:
    travel_products = json.load(f)

# Conversation states
START = "start_conversation"
USER_INPUT = "user_input"
INTENT_CLARITY = "intent_clarity"
INTENT_CONFIRMATION = "intent_confirmation"
PRODUCT_INFO_EXTRACTION = "product_info_extraction"
PRODUCT_RECOMMENDATION = "product_recommendation"
END_CONVERSATION = "end_conversation"

# Store conversation history
conversation_histories = {}

@app.route('/')
def index():
    # Generate a unique session ID if not already present
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        conversation_histories[session['session_id']] = []
        session['state'] = START
    
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    session_id = session.get('session_id')
    current_state = session.get('state', START)
    
    # Add user message to conversation history
    conversation_histories[session_id].append({"role": "user", "content": user_message})
    
    # Check for non-Indian destinations
    non_indian_request = check_non_indian_destination(user_message)
    if non_indian_request and current_state != START:
        response = "I'm specialized in Indian pilgrimage destinations only. Would you like me to suggest some popular pilgrimage sites in India instead?"
        conversation_histories[session_id].append({"role": "assistant", "content": response})
        return jsonify({'message': response, 'state': session['state']})
    
    # Process based on current state
    if current_state == START:
        # Format welcome message with proper paragraphs
        response = handle_start_conversation()
        session['welcome_shown'] = True
        session['state'] = USER_INPUT
    elif current_state == USER_INPUT:
        response = handle_user_input(user_message, session_id)
        session['state'] = INTENT_CLARITY
    elif current_state == INTENT_CLARITY:
        response, is_clear = handle_intent_clarity(user_message, session_id)
        if is_clear:
            session['state'] = INTENT_CONFIRMATION
        else:
            # Stay in INTENT_CLARITY if intent is not clear
            pass
    elif current_state == INTENT_CONFIRMATION:
        response, is_confirmed = handle_intent_confirmation(user_message, session_id)
        if is_confirmed:
            session['state'] = PRODUCT_INFO_EXTRACTION
        else:
            # Go back to INTENT_CLARITY if intent is not confirmed
            session['state'] = INTENT_CLARITY
    elif current_state == PRODUCT_INFO_EXTRACTION:
        response, products = handle_product_info_extraction(user_message, session_id)
        if products:
            session['recommended_products'] = products
            session['state'] = PRODUCT_RECOMMENDATION
        else:
            # Stay in PRODUCT_INFO_EXTRACTION if more info is needed
            pass
    elif current_state == PRODUCT_RECOMMENDATION:
        response, is_satisfied = handle_product_recommendation(user_message, session_id)
        if is_satisfied:
            session['state'] = END_CONVERSATION
        else:
            # Go back to INTENT_CLARITY for a new search
            session['state'] = INTENT_CLARITY
    elif current_state == END_CONVERSATION:
        response = handle_end_conversation()
        # Reset to start a new conversation
        session['state'] = START
    
    # Add assistant response to conversation history
    conversation_histories[session_id].append({"role": "assistant", "content": response})
    
    # Format response for proper display
    formatted_response = format_response(response)
    
    return jsonify({'message': formatted_response, 'state': session['state']})

def format_response(response):
    """Format the response for better display in the chat interface"""
    # Convert newlines to HTML breaks
    formatted = response.replace('\n\n', '<br><br>').replace('\n', '<br>')
    
    # Format lists if present
    if '- ' in formatted:
        formatted = re.sub(r'<br>- ', '<br>• ', formatted)
    
    return formatted

def check_non_indian_destination(message):
    """Check if the user is asking about non-Indian destinations"""
    non_indian_countries = ['usa', 'america', 'australia', 'europe', 'africa', 'china', 'japan', 'thailand', 
                           'singapore', 'malaysia', 'uk', 'united kingdom', 'canada', 'mexico', 'brazil', 'russia']
    return any(country in message.lower() for country in non_indian_countries)


def format_response(response):
    """Format the response for better display in the chat interface"""
    # Convert newlines to HTML breaks
    formatted = response.replace('\n\n', '<br><br>').replace('\n', '<br>')
    
    # Format lists if present
    if '- ' in formatted:
        formatted = re.sub(r'<br>- ', '<br>• ', formatted)
    
    return formatted

def check_non_indian_destination(message):
    """Check if the user is asking about non-Indian destinations"""
    non_indian_countries = ['usa', 'america', 'australia', 'europe', 'africa', 'china', 'japan', 'thailand', 
                           'singapore', 'malaysia', 'uk', 'united kingdom', 'canada', 'mexico', 'brazil', 'russia']
    return any(country in message.lower() for country in non_indian_countries)

def handle_start_conversation():
    return "Namaste! 🙏 I'm your Indian Pilgrimage Travel Assistant.\n\nI can help you plan spiritual journeys to sacred destinations across India including temples, holy rivers, historic religious sites, and more.\n\nWould you like to explore famous pilgrimage circuits like Char Dham, discover temples in South India, visit the holy cities of Varanasi or Haridwar, or learn about other sacred places?"

def handle_user_input(message, session_id):
    # Initial response to user input to move to intent clarity phase
    return "Thank you for sharing your interest in Indian pilgrimages. To help you plan the perfect spiritual journey, could you tell me more about:\n\n- Which region of India you're interested in (North, South, East, West)\n- When you're planning to travel\n- How many days you can spend\n- If you're interested in specific deities or religious traditions (Hindu, Buddhist, Jain, Sikh, etc.)\n- Any specific spiritual experiences you're seeking"

def handle_intent_clarity(message, session_id):
    # Use OpenAI to determine if the user's intent is clear
    conversation = conversation_histories[session_id]
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an Indian pilgrimage travel planning assistant. Determine if the user's travel intent is clear. Extract travel preferences like pilgrimage region (North/South/East/West India), specific temples or sites, religious tradition (Hindu/Buddhist/Jain/Sikh), travel dates, group size, and accommodation preferences (luxury/mid-range/budget). Focus ONLY on Indian pilgrimage destinations. If any key information is missing, ask for it. If you have enough information, say 'INTENT_CLEAR: yes' at the end of your response. Otherwise, say 'INTENT_CLEAR: no'."},
            *conversation
        ]
    )
    
    ai_response = response.choices[0].message.content
    
    # Check if intent is clear
    is_clear = "INTENT_CLEAR: yes" in ai_response
    # Remove the INTENT_CLEAR tag from the response
    clean_response = ai_response.replace("INTENT_CLEAR: yes", "").replace("INTENT_CLEAR: no", "").strip()
    
    return clean_response, is_clear

def handle_intent_confirmation(message, session_id):
    # Use OpenAI to confirm the user's intent
    conversation = conversation_histories[session_id]
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an Indian pilgrimage travel planning assistant. Based on the conversation, summarize the user's pilgrimage preferences and ask them to confirm if you understood correctly. Include key details like specific religious sites, region of India, spiritual significance, budget, dates, and accommodations. Focus ONLY on Indian pilgrimage destinations. At the end of your response, add 'IS_CONFIRMED: yes' if the user confirms your understanding or 'IS_CONFIRMED: no' if they correct or add information."},
            *conversation
        ]
    )
    
    ai_response = response.choices[0].message.content
    
    # Check if intent is confirmed
    is_confirmed = "IS_CONFIRMED: yes" in ai_response
    # Remove the confirmation tag from the response
    clean_response = ai_response.replace("IS_CONFIRMED: yes", "").replace("IS_CONFIRMED: no", "").strip()
    
    return clean_response, is_confirmed

def handle_product_info_extraction(message, session_id):
    # Use OpenAI to extract product information based on user preferences
    conversation = conversation_histories[session_id]
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an Indian pilgrimage travel planning assistant with access to a pilgrimage package database. Based on the user's preferences, identify key criteria to search for matching pilgrimage packages. Focus ONLY on Indian pilgrimage destinations. Format your output as a friendly response followed by a JSON object with search criteria, e.g., SEARCH_CRITERIA: {\"region\": \"north\", \"religion\": \"hindu\", \"budget\": \"medium\", \"duration\": \"1 week\"}. Ask any final questions needed to refine your search."},
            *conversation
        ]
    )
    
    ai_response = response.choices[0].message.content
    
    # Extract search criteria if present
    search_criteria_match = re.search(r'SEARCH_CRITERIA: ({.*})', ai_response, re.DOTALL)
    
    products = []
    if search_criteria_match:
        try:
            search_criteria = json.loads(search_criteria_match.group(1))
            # Filter products based on search criteria
            # This is a simplified matching logic; in a real app, you'd use more sophisticated matching
            products = filter_products(search_criteria)
            
            # Remove the search criteria from the response
            clean_response = ai_response.replace(search_criteria_match.group(0), "").strip()
        except json.JSONDecodeError:
            clean_response = "I'm having trouble processing your preferences. Let's try again. " + ai_response
    else:
        clean_response = ai_response
    
    return clean_response, products

def filter_products(criteria):
    # Simple product filtering logic
    filtered_products = []
    
    for product in travel_products:
        matches = True
        for key, value in criteria.items():
            if key in product and product[key] != value:
                if key == "budget":
                    # Special handling for budget ranges
                    budget_levels = {"low": 1, "medium": 2, "high": 3, "luxury": 4}
                    if budget_levels.get(product[key], 0) > budget_levels.get(value, 0):
                        matches = False
                elif key == "religion" or key == "region":
                    # Special handling for religion and region - partial matching
                    if value.lower() not in product[key].lower():
                        matches = False
                else:
                    matches = False
        
        if matches:
            filtered_products.append(product)
    
    # Return top 3 products
    return filtered_products[:3]

def handle_product_recommendation(message, session_id):
    # Use OpenAI to present recommendations and check if user is satisfied
    conversation = conversation_histories[session_id]
    recommended_products = session.get('recommended_products', [])
    
    # Add product information to the conversation
    product_info = "Based on your pilgrimage preferences, I found these divine journeys for you:\n"
    for i, product in enumerate(recommended_products, 1):
        product_info += f"\n{i}. {product['name']} - {product['description']} - ${product['price']}/person\n"
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a travel planning assistant. Present the recommended products to the user in a helpful way. Here are the products: {product_info} Ask if they're satisfied with these options or want to explore more. Include 'USER_SATISFIED: yes' at the end if the user indicates satisfaction with the recommendations, or 'USER_SATISFIED: no' if they want to see more options or have different preferences."},
            *conversation,
            {"role": "assistant", "content": product_info}
        ]
    )
    
    ai_response = response.choices[0].message.content
    
    # Check if user is satisfied
    is_satisfied = "USER_SATISFIED: yes" in ai_response
    # Remove the satisfaction tag from the response
    clean_response = ai_response.replace("USER_SATISFIED: yes", "").replace("USER_SATISFIED: no", "").strip()
    
    return clean_response, is_satisfied

def handle_end_conversation():
    return "Om Shanti! 🙏 Thank you for using our Indian Pilgrimage Planner. Your spiritual journey has been saved. May your pilgrimage be filled with divine blessings and inner peace. Is there anything else you'd like help with for your sacred journey?"

if __name__ == '__main__':
    app.run(debug=True)
