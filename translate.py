import requests

def translate(text):
    url = 'https://translate.yandex.net/api/v1.5/tr.json/translate'

    params = {
        'key': 'trnsl.1.1.20190413T111416Z.1abf50c982ce4f9e.2b978b4abcdb550558af2b2b9fdb162f36ff06fd',
        'text': text,
        'lang': 'ru-en',
        'format': 'plain'
    }
    response = requests.get(url, params)
    json = response.json()
    return json['text'][0]
