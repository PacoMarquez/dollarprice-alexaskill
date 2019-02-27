from __future__ import print_function
import requests
import os
from decimal import Decimal

# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_ssml_response(title, output, reprompt_text, should_end_session, content_output):
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': content_output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'SSML',
                'ssml': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

# --------------- Functions that control the request to thir vendor ---------------


def get_api_key():
    return os.environ['api_layer_key']


def build_endpoint(country_code):
    api_key = get_api_key()
    url = "http://apilayer.net/api/live?access_key={0}&currencies={1}&source=USD&format=1".format(api_key, country_code)
    return url


def send_request(country_code):
    try:
        url = build_endpoint(country_code)
        response = requests.post(url)
        return get_value_from_response(response.json())
    except Exception as ex:
        print(str(ex))


def get_value_from_response(response):
    if response['quotes'] is not None:
        dolar_value = next(iter(response['quotes'].values()))
        dolar_value_format = Decimal(dolar_value)
        return round(dolar_value_format,2)
    else:
        return -1


def get_price_from_service(country_code):
    return send_request(country_code)

# --------------- Functions that control the skill's behavior ------------------


def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Bienvenido"
    content_output = "Bienvenidos a el Precio del Dólar. " \
                     "Por Favor indícame de que país quieres hacer la " \
                     "conversión diciendo, por ejemplo: " \
                     "¿Cuál es el precio del dólar en México?"


    speech_output = "<speak>" + content_output + "</speak>"


    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "<speak>Por favor indícame de que país quieres conocer el " \
                    "precio del dólar actual diciendo, por ejemplo: " \
                    "¿Cuál es el precio del dólar en México?</speak>"

    should_end_session = False
    return build_response(session_attributes, build_ssml_response(
        card_title, speech_output, reprompt_text, should_end_session, content_output))


def handle_session_end_request():
    card_title = "Sesion Terminada"
    speech_output = "Gracias por usar El Precio del Dólar. Hasta luego" \

    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

country_codes = {
        'mexico': 'MXN',
        'canada': 'CAD',
        'colombia': 'COP',
        'venezuela': 'VEB',
        'argentina': 'ARS',
        'chile': 'CLP'
    }

country_correct_names = {
        'mexico': 'México',
        'canada': 'Canadá',
        'colombia': 'Colombia',
        'venezuela': 'Venezuela',
        'argentina': 'Argentina',
        'chile': 'Chile'
    }


def get_country_correct_name(country_input):
    return country_correct_names[country_input]


def get_country_currency_abbreviation(country_input):
    return country_codes[country_input]


def get_currency_simbol(country_input):
    return country_codes[country_input]


def get_list_names_of_countries():
    country_names = ""
    for i, item in enumerate(country_correct_names):
        if i == len(country_correct_names) - 1:
            country_names = country_names[:-2]
            country_names += " y " + country_correct_names[item]
        else:
            country_names += country_correct_names[item] + ", "

    return country_names


def validate_country(intent):
    status_from_request = intent['slots']['country']['resolutions']['resolutionsPerAuthority'][0]['status']['code']
    print(status_from_request)
    return status_from_request == "ER_SUCCESS_MATCH"


def get_dollar_price_by_country(intent, session):
    card_title = "Get Dollar Price"
    session_attributes = {}
    speech_output = "No estoy seguro de que país estas hablando. " \
                    "Por favor inténtalo nuevamente."
    reprompt_text = "No estoy seguro de que país estas hablando. " \
                    "Por favor indícame de que país quieres conocer el " \
                    "precio del dólar actual diciendo, por ejemplo, " \
                    "¿Cuál es el precio del dólar en México?"

    if 'country' in intent['slots']:
        if 'value' not in intent['slots']['country']:
            should_end_session = True
        elif validate_country(intent):
            country_input = intent['slots']['country']['value']
            dollar_value = get_price_from_service(get_country_currency_abbreviation(country_input))
            speech_output = "El valor del dólar en " + get_country_correct_name(country_input) + \
                            " es de " + get_currency_simbol(country_input) + str(dollar_value) + \
                            ". Hasta luego."
            reprompt_text = None
            should_end_session = True
        else:
            should_end_session = False
    else:
        should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_available_countries(intent, session):
    card_title = "Get Available Countries"
    session_attributes = {}
    countries = get_list_names_of_countries()
    speech_output = "Los países disponibles para esta aplicación son: " + countries
    reprompt_text = None
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "DllPriceMxIntent":
        return get_dollar_price_by_country(intent, session)
    elif intent_name == "DllPriceMxListIntent":
        return get_available_countries(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
