from flask import Flask, request
import logging
import json
import random
import requests

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': {'img': ['965417/1ee36d44797cb85cdf4b', '1521359/67c027400ec86fa1c3d4'], 'country': ['россия',
                                                                                                   'российская федерация']},
    'нью-йорк': {'img': ['1521359/fce264390c18c4cbfd78', '1540737/c1c4a33836aa5e777b6e'], 'country': ['сша',
                                                                                                      'соединенные штаты америки',
                                                                                                      'соединённые штаты америки']},
    'париж': {'img': ["965417/500a6d82dc58134c61d1", '997614/39cce1afc1d77605d66e'], 'country': ['франция']}
}

sessionStorage = {}

words = open('/home/IGragon/mysite/words.txt', encoding='UTF-8', mode='r')
words = list(map(str.strip, words.readlines()))


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
        res['response']['text'] = 'Привет, я Алиса! Назови своё имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'option': None,
            'game_started': False,
            'words': words,
            'word': None,
            'fake_words': []
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. Выбирай, что хочешь делать!'
            res['response']['buttons'] = [
                {
                    'title': 'Игра "Угадай перевод"',
                    'hide': True
                },
                {
                    'title': 'Переводчик',
                    'hide': True
                },
                {
                    'title': 'Расчет расстояния',
                    'hide': True
                },
                {
                    'title': 'Хочу выйти!',
                    'hide': True
                },
                {
                    'title': 'Помощь',
                    'hide': False
                }
            ]

    else:
        if not sessionStorage[user_id]['option']:
            if 'Игра "Угадай перевод"' in req['request']['original_utterance']:
                sessionStorage[user_id]['option'] = 'game'
                game_translation(res, req)
            elif 'Переводчик"' in req['request']['original_utterance']:
                sessionStorage[user_id]['option'] = 'translate'
                res['response']['text'] = ' Нажми "Помощь" чтобы узнать как работает "Переводчик" '
                translator(res, req)
            elif 'Расчет расстояния"' in req['request']['original_utterance']:
                sessionStorage[user_id]['option'] = 'distance'
                res['response']['text'] = ' Нажми "Помощь" чтобы узнать как работает "Расчёт расстояния" '
                distance(res, req)
            elif 'Хочу выйти!' in req['request']['original_utterance']:
                res['response']['text'] = 'Пока, {}!'.format(sessionStorage[user_id]['first_name'])
                res['end_session'] = True
            elif 'помощь' in req['request']['nlu']['tokens']:
                res['response']['text'] = ''' Игра "Угадай перевод" - вам даётся слово на случайном языке
                 и варианты перевода\nПереводчик - перевод фраз и слов\nРасчёт расстояния - расчёт расстояния
                  от адреса до адреса\nХочу выйти - завершение диалога.'''
                res['response']['buttons'] = [
                    {
                        'title': 'Игра "Угадай перевод"',
                        'hide': True
                    },
                    {
                        'title': 'Переводчик',
                        'hide': True
                    },
                    {
                        'title': 'Расчет расстояния',
                        'hide': True
                    },
                    {
                        'title': 'Хочу выйти!',
                        'hide': True
                    },
                    {
                        'title': 'Помощь',
                        'hide': False
                    }
                ]
            else:
                res['response']['text'] = '{}, повтори пожалуйста!'.format(sessionStorage[user_id]['first_name'])
                res['response']['buttons'] = [
                    {
                        'title': 'Игра "Угадай перевод"',
                        'hide': True
                    },
                    {
                        'title': 'Переводчик',
                        'hide': True
                    },
                    {
                        'title': 'Расчет расстояния',
                        'hide': True
                    },
                    {
                        'title': 'Хочу выйти!',
                        'hide': True
                    },
                    {
                        'title': 'Помощь',
                        'hide': False
                    }
                ]
        else:
            if sessionStorage[user_id]['option'] == 'game':
                game_translation(res, req)
            elif sessionStorage[user_id]['option'] == 'translate':
                translator(res, req)
            elif sessionStorage[user_id]['option'] == 'distance':
                distance(res, req)


def game_translation(res, req):
    user_id = req['session']['user_id']
    res['response']['buttons'] = [
        {
            'title': 'Алиса, помощь',
            'hide': False
        }
    ]
    if req['request']['original_utterance'] == 'Игра "Угадай перевод"':
        res['response']['text'] = ' Нажми "Помощь" чтобы узнать как играть '
        return
    if not sessionStorage[user_id]['game_started'] and req['request']['original_utterance'] == 'Алиса, помощь':
        res['response']['text'] = 'Нажми "Начать", чтобы начать игру\nЛибо напишите "Алиса, выход", чтобы выйти'
        res['response']['buttons'] += [
            {
                'title': 'Начать'
            }
        ]
    elif req['request']['original_utterance'] == 'Алиса, выход':
        sessionStorage[user_id]['game_started'] = False
        sessionStorage[user_id]['option'] = False
        res['response']['buttons'].clear()
        res['response']['text'] = '{}, Вы вышли в выбор действий, выбирайте!'.format(
            sessionStorage[user_id]['first_name'])
    else:
        if req['request']['original_utterance'] == 'Начать' and not sessionStorage[user_id]['game_started']:
            sessionStorage[user_id]['game_started'] = True
            sessionStorage[user_id]['word'] = random.choice(sessionStorage[user_id]['words'])
            while len(res['response']['buttons']) != 5:
                word = random.choice(sessionStorage[user_id]['words'])
                if word != sessionStorage[user_id]['word']:
                    res['response']['buttons'].append({
                        'title': word,
                        'hide': False
                    })
            len_buttons = len(res['response']['buttons']) - 1
            res['response']['buttons'].insert({
                'title': sessionStorage[user_id]['word'],
                'hide': False
            },
                random.randint(0, len_buttons) + 1)
            info = get_word(sessionStorage[user_id]['word'])
            res['response']['text'] = 'Вам выпало слово - {}\nНа языке {}\nКак думаете, какой перевод?'.format(
                info[0], info[1])
        elif req['request']['original_utterance'] == 'Алиса, помощь':
            res['response']['text'] = '{}, выбери перевод из предложенных вариантов'.format(
                sessionStorage[user_id]['first_name'])
        elif req['request']['original_utterance'] != sessionStorage[user_id]['word']:
            res['response']['text'] = 'Нет, у этого слова другой перевод!'
        elif req['request']['original_utterance'] == sessionStorage[user_id]['word']:
            res['response']['text'] = '{}, молодец, ты справился!!'.format(sessionStorage[user_id]['first_name'])


def translator(res, req):
    user_id = req['session']['user_id']
    res['response']['buttons'] = [
        {
            'title': 'Помощь',
            'hide': True
        }
    ]
    pass


def distance(res, req):
    user_id = req['session']['user_id']
    res['response']['buttons'] = [
        {
            'title': 'Помощь',
            'hide': True
        }
    ]
    pass


def get_city(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO, то пытаемся получить город(city), если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('city', None)


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


def get_word(word):
    languages = {
        'азербайджанский': 'az', 'албанский': 'sq', 'английский': 'en', 'арабский': 'ar', 'башкирский': 'ba',
        'белорусский': 'be', 'болгарский': 'bg', 'валлийский': 'cy', 'вьетнамский': 'vi', 'греческий': 'el',
        'грузинский': 'ka', 'датский': 'da', 'ирландский': 'ga', 'итальянский': 'it', 'исландский': 'is',
        'испанский': 'es', 'казахский': 'kk', 'китайский': 'zh', 'корейский': 'ko', 'латынь': 'la', 'латышский': 'lv',
        'немецкий': 'de', 'норвежский': 'no', 'персидский': 'fa', 'польский': 'pl', 'португальский': 'pt',
        'румынский': 'ro', 'сербский': 'sr', 'словацкий': 'sk', 'словенский': 'sl', 'тайский': 'th', 'турецкий': 'tr',
        'украинский': 'uk', 'финский': 'fi', 'французский': 'fr', 'хинди': 'hi', 'хорватский': 'hr', 'чешский': 'cs',
        'шведский': 'sv', 'шотландский': 'gd', 'эстонский': 'et', 'эсперанто': 'eo', 'японский': 'ja'
    }

    url = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
    lang = random.choice(languages)
    params = {
        'key': 'trnsl.1.1.20190413T111416Z.1abf50c982ce4f9e.2b978b4abcdb550558af2b2b9fdb162f36ff06fd',
        'text': word,
        'lang': 'ru-{}'.format(languages[lang]),
        'format': 'plain'
    }

    response = requests.get(url, params)
    json = response.json()

    return json['text'][0], lang


if __name__ == '__main__':
    app.run()
