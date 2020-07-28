import os
from flask import Flask, request, jsonify, session
import uuid
import dialogflow_v2 as dialogflow
from flask_cors import CORS
from iss_io import current_location, next_pass, people

app = Flask(__name__)
app.config.from_object("config")
CORS(app)

session_client = dialogflow.SessionsClient()

API_URL = 'http://api.open-notify.org/'


def simple_session(function):
    def wrapper(*args, **kwargs):
        if not session.get('session_token'):
            session['session_token'] = str(uuid.uuid4())
        return function(*args, **kwargs)
    return wrapper


@app.route('/', methods=['GET'])
@simple_session
def home():
    # get the text query passed via url and default to ' ' (this triggers a default response)
    text = request.args.get('text', ' ')
    # pass the text to the dialogflow api
    text_input = dialogflow.types.TextInput(
        text=text, language_code='en')
    query_input = dialogflow.types.QueryInput(text=text_input)
    session_path = session_client.session_path(
        'iss-dialog', session['session_token'])

    # find the intent: it will be one of Location, Pass, Crew, or Default.
    response = session_client.detect_intent(
        session=session_path, query_input=query_input)
    intent = response.query_result.intent.display_name
    response_text = response.query_result.fulfillment_text

    if(intent == 'Location'):
        response_text = current_location()
    elif(intent == 'Pass'):
        # this is the tricky one, if the intent matches we'll have parameters
        parameters = response.query_result.parameters.fields
        lat = parameters.get('latitude').number_value
        lon = parameters.get('longitude').number_value
        # sometimes coordinates have ordinal values(North, South, East, West), there's a lot of room for improvement here
        if parameters.get('northsouth').string_value and parameters.get('northsouth').string_value[0].lower() == 's':
            lat = lat * -1
        if parameters.get('eastwest').string_value and parameters.get('eastwest').string_value[0].lower() == 'w':
            lon = lon * -1
        if not lat or not lon:
            response_text = 'Sorry, I couldn\'t make out those coordinates'
        else:
            response_text = next_pass(lat, lon)
    elif(intent == 'Crew'):
        response_text = people()

    return jsonify({
        'text': response_text
    })
