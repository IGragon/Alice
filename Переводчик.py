from translate import translate
from flask import Flask, request
import logging
import json

app = Flask(__name__)

@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return json.dumps(response)

def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Напиши "Переведи слово - <слово>", и я его переведу на английский!'
        return
    else:
        word = translate(req['request']['nlu']['tokens'][-1])
        res['response']['text'] = word
