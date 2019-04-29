from flask import Flask, request
import logging
import json
import random
import requests

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

languages = {
    'азербайджанский': 'az', 'албанский': 'sq', 'английский': 'en', 'арабский': 'ar', 'башкирский': 'ba',
    'белорусский': 'be', 'болгарский': 'bg', 'валлийский': 'cy', 'вьетнамский': 'vi', 'греческий': 'el',
    'грузинский': 'ka', 'датский': 'da', 'ирландский': 'ga', 'итальянский': 'it', 'исландский': 'is',
    'испанский': 'es', 'казахский': 'kk', 'китайский': 'zh', 'корейский': 'ko', 'латынь': 'la', 'латышский': 'lv',
    'немецкий': 'de', 'норвежский': 'no', 'персидский': 'fa', 'польский': 'pl', 'португальский': 'pt',
    'румынский': 'ro', 'сербский': 'sr', 'словацкий': 'sk', 'словенский': 'sl', 'тайский': 'th', 'турецкий': 'tr',
    'украинский': 'uk', 'финский': 'fi', 'французский': 'fr', 'хинди': 'hi', 'хорватский': 'hr', 'чешский': 'cs',
    'шведский': 'sv', 'шотландский': 'gd', 'эстонский': 'et', 'эсперанто': 'eo', 'японский': 'ja', 'русский': 'ru'
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
            'translate': False,
            'choose_language_1': False,
            'choose_language_2': False,
            'lang1': False,
            'lang2': False
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name.title()
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
            elif 'Переводчик' in req['request']['original_utterance']:
                sessionStorage[user_id]['option'] = 'translate'
                translator(res, req)
            elif 'Хочу выйти!' in req['request']['original_utterance']:
                res['response']['text'] = 'Пока, {}!'.format(sessionStorage[user_id]['first_name'])
                res['end_session'] = True
            elif 'помощь' in req['request']['nlu']['tokens']:
                res['response']['text'] = ''' Игра "Угадай перевод" - вам даётся слово на случайном языке
                 и варианты перевода\n\n
                 Переводчик - перевод фраз и слов\n\n
                 Хочу выйти - завершение диалога.'''
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


def game_translation(res, req):
    user_id = req['session']['user_id']
    res['response']['buttons'] = [
        {
            'title': 'Алиса, помощь',
            'hide': False
        },
        {
            'title': 'Алиса, выход',
            'hide': True
        }
    ]
    if req['request']['original_utterance'] == 'Игра "Угадай перевод"':
        res['response']['text'] = ' Нажми "Алиса, помощь", если не знаешь, что делать'
        res['response']['buttons'].append(
            {
                'title': 'Начать',
                'hide': True
            }
        )
        return
    elif not sessionStorage[user_id]['game_started'] and req['request']['original_utterance'] == 'Алиса, помощь':
        res['response']['text'] = 'Нажми "Начать", чтобы начать игру\n' \
                                  'Либо нажмите "Алиса, выход", чтобы выйти\n\n' \
                                  'Тебе даётся случайное слово на случайном языке. Попробуй угадать!'
        res['response']['buttons'].append(
            {
                'title': 'Начать',
                'hide': True
            }
        )
    elif req['request']['original_utterance'] == 'Алиса, выход':
        sessionStorage[user_id]['game_started'] = False
        sessionStorage[user_id]['option'] = False
        res['response']['buttons'].clear()
        res['response']['text'] = '{}, Вы вышли в выбор действий, выбирайте!'.format(
            sessionStorage[user_id]['first_name'])
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
        if req['request']['original_utterance'] == 'Начать' and not sessionStorage[user_id]['game_started']:
            sessionStorage[user_id]['game_started'] = True
            info = get_word()
            sessionStorage[user_id]['word'] = info[0]
            while len(res['response']['buttons']) != 6:
                word = random.choice(sessionStorage[user_id]['words'])
                if word != sessionStorage[user_id]['word']:
                    res['response']['buttons'].append({
                        'title': word,
                        'hide': True
                    })
            len_buttons = len(res['response']['buttons']) - 2
            res['response']['buttons'].insert(random.randint(1, len_buttons) + 1,
                                              {
                                                  'title': sessionStorage[user_id]['word'],
                                                  'hide': True
                                              })
            res['response']['text'] = 'Вам выпало слово - {}\nНа языке {}\nКак думаете, какой перевод?'.format(
                info[1], info[2])
            sessionStorage[user_id]['buttons'] = res['response']['buttons'].copy()
        elif req['request']['original_utterance'] == 'Алиса, помощь':
            res['response']['text'] = '{}, выбери перевод из предложенных вариантов, у тебя всего 3 попытки!'.format(
                sessionStorage[user_id]['first_name'])
        elif sessionStorage[user_id]['word'] and req['request']['original_utterance'] != sessionStorage[user_id][
            'word']:
            res['response']['text'] = 'Нет, у этого слова другой перевод!'
            sessionStorage[user_id]['buttons'].remove({
                'title': req['request']['original_utterance'],
                'hide': True
            })
            res['response']['buttons'] = sessionStorage[user_id]['buttons'].copy()
            if len(res['response']['buttons']) - 1 < 4:
                res['response']['text'] = f'Эх, не удалось тебе отгадать!\n' \
                    f'Это было слово "{sessionStorage[user_id]["word"]}"'
                sessionStorage[user_id]['game_started'] = False
                res['response']['buttons'] = sessionStorage[user_id]['buttons'][:2]
                res['response']['buttons'].append(
                    {
                        'title': 'Начать',
                        'hide': True
                    }
                )
                sessionStorage[user_id]['word'] = False
                return
        elif req['request']['original_utterance'] == sessionStorage[user_id]['word']:
            res['response']['text'] = '{}, молодец, ты справился!!\n' \
                                      'Нажми "Начать", чтобы сыграть заного, либо "Алиса, выход", чтобы выйти.'.format(
                sessionStorage[user_id]['first_name'])
            res['response']['buttons'].append(
                {
                    'title': 'Начать',
                    'hide': True
                }
            )
            sessionStorage[user_id]['game_started'] = False
        else:
            res['response']['text'] = 'Хм, какая - то незнакомая комманда, повтори ещё раз!'


def translator(res, req):
    user_id = req['session']['user_id']
    res['response']['buttons'] = [
        {
            'title': 'Алиса, помощь',
            'hide': False
        },
        {
            'title': 'Алиса, выход',
            'hide': True
        }
    ]
    if (not sessionStorage[user_id]['choose_language_1'] and not sessionStorage[user_id]['choose_language_2'] and
       not sessionStorage[user_id]['translate']) and req['request']['original_utterance'] == 'Переводчик':
        res['response']['text'] = ' Нажми "Алиса, помощь", если не знаешь, что делать'
        res['response']['buttons'] += [
            {
                'title': 'Язык1',
                'hide': 'True'
            },
            {
                'title': 'Язык2',
                'hide': 'True'
            },
            {
                'title': 'Перевод',
                'hide': 'True'
            }
        ]
        return
    elif (not sessionStorage[user_id]['choose_language_1'] and not sessionStorage[user_id]['choose_language_2'] and
          not sessionStorage[user_id]['translate'] and req['request']['original_utterance'] == 'Алиса, выход'):
        sessionStorage[user_id]['game_started'] = False
        sessionStorage[user_id]['option'] = False
        res['response']['buttons'].clear()
        res['response']['text'] = '{}, Вы вышли в выбор действий, выбирайте!'.format(
            sessionStorage[user_id]['first_name'])
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
                'title': 'Хочу выйти!',
                'hide': True
            },
            {
                'title': 'Помощь',
                'hide': False
            }
        ]
    elif (not sessionStorage[user_id]['choose_language_1'] and not sessionStorage[user_id]['choose_language_2'] and
          not sessionStorage[user_id]['translate'] and req['request']['original_utterance'] == 'Алиса, помощь'):
        res['response']['text'] = 'Нажми "Перевод" и введи текст, чтобы его перевести\n' \
                                  'Нажми "Язык1", чтобы выбрать с какого языка переводить\n' \
                                  'Нажми "Язык2", чтобы выбрать на какой язык переводить\n' \
                                  'Либо нажмите "Алиса, выход", чтобы выйти'
        res['response']['buttons'] += [
            {
                'title': 'Язык1',
                'hide': 'True'
            },
            {
                'title': 'Язык2',
                'hide': 'True'
            },
            {
                'title': 'Перевод',
                'hide': 'True'
            }
        ]
    elif (not sessionStorage[user_id]['choose_language_1'] and not sessionStorage[user_id]['choose_language_2'] and
          not sessionStorage[user_id]['translate'] and req['request']['original_utterance'] == 'Язык1'):
        sessionStorage[user_id]['choose_language_1'] = True
        res['response']['text'] = 'Выберите из предложенных вариантов!'
        res['response']['buttons'].clear()
        for lang in list(languages):
            res['response']['buttons'].append(
                {
                    'title': lang,
                    'hide': True
                }
            )
    elif (not sessionStorage[user_id]['choose_language_1'] and not sessionStorage[user_id]['choose_language_2'] and
          not sessionStorage[user_id]['translate'] and req['request']['original_utterance'] == 'Язык2'):
        sessionStorage[user_id]['choose_language_2'] = True
        res['response']['text'] = 'Выберите из предложенных вариантов!'
        res['response']['buttons'].clear()
        for lang in list(languages):
            res['response']['buttons'].append(
                {
                    'title': lang,
                    'hide': True
                }
            )
    elif sessionStorage[user_id]['choose_language_1']:
        if req['request']['original_utterance'] in list(languages):
            sessionStorage[user_id]['lang1'] = languages[req['request']['original_utterance']]
            sessionStorage[user_id]['choose_language_1'] = False
            res['response']['text'] = 'Язык1 успешно выбран'
            res['response']['buttons'] += [
                {
                    'title': 'Язык1',
                    'hide': 'True'
                },
                {
                    'title': 'Язык2',
                    'hide': 'True'
                },
                {
                    'title': 'Перевод',
                    'hide': 'True'
                }
            ]
        else:
            res['response']['text'] = 'Выберите из предложенных вариантов!'
            res['response']['buttons'].clear()
            for lang in list(languages):
                res['response']['buttons'].append(
                    {
                        'title': lang,
                        'hide': True
                    }
                )
    elif sessionStorage[user_id]['choose_language_2']:
        if req['request']['original_utterance'] in list(languages):
            sessionStorage[user_id]['lang2'] = languages[req['request']['original_utterance']]
            sessionStorage[user_id]['choose_language_2'] = False
            res['response']['text'] = 'Язык2 успешно выбран'
            res['response']['buttons'] += [
                {
                    'title': 'Язык1',
                    'hide': 'True'
                },
                {
                    'title': 'Язык2',
                    'hide': 'True'
                },
                {
                    'title': 'Перевод',
                    'hide': 'True'
                }
            ]
        else:
            res['response']['text'] = 'Выберите из предложенных вариантов!'
            res['response']['buttons'].clear()
            for lang in list(languages):
                res['response']['buttons'].append(
                    {
                        'title': lang,
                        'hide': True
                    }
                )
    elif (not sessionStorage[user_id]['choose_language_1'] and not sessionStorage[user_id]['choose_language_2'] and
          not sessionStorage[user_id]['translate'] and req['request']['original_utterance'] == 'Перевод'):
        if not sessionStorage[user_id]['lang1'] or not sessionStorage[user_id]['lang2']:
            res['response']['text'] = 'Убедись, что языки выбраны!'
            res['response']['buttons'] += [
                {
                    'title': 'Язык1',
                    'hide': 'True'
                },
                {
                    'title': 'Язык2',
                    'hide': 'True'
                },
                {
                    'title': 'Перевод',
                    'hide': 'True'
                }
            ]
            return
        sessionStorage[user_id]['translate'] = True
        res['response']['text'] = 'Введите фразу для перевода!'
        res['response']['buttons'].clear()

    elif sessionStorage[user_id]['translate']:
        res['response']['text'] = translate(req['request']['original_utterance'],
                                            sessionStorage[user_id]['lang1'],
                                            sessionStorage[user_id]['lang2'])
        sessionStorage[user_id]['translate'] = False
        res['response']['buttons'] += [
            {
                'title': 'Язык1',
                'hide': 'True'
            },
            {
                'title': 'Язык2',
                'hide': 'True'
            },
            {
                'title': 'Перевод',
                'hide': 'True'
            }
        ]
    else:
        res['response']['text'] = 'Хм, какая - то незнакомая комманда, повтори ещё раз!'


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


def get_word():
    word = random.choice(words)
    trans_word = word
    lang = ''
    while trans_word == word:
        word = random.choice(words)
        url = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
        lang = random.choice(sorted(list(languages)[:-1]))
        params = {
            'key': 'trnsl.1.1.20190413T111416Z.1abf50c982ce4f9e.2b978b4abcdb550558af2b2b9fdb162f36ff06fd',
            'text': word,
            'lang': 'ru-{}'.format(languages[lang]),
            'format': 'plain'
        }

        response = requests.get(url, params)
        json = response.json()
        trans_word = json['text'][0]

    return word, trans_word, lang


def translate(text, lang1, lang2):

    url = 'https://translate.yandex.net/api/v1.5/tr.json/translate'

    params = {
        'key': 'trnsl.1.1.20190413T111416Z.1abf50c982ce4f9e.2b978b4abcdb550558af2b2b9fdb162f36ff06fd',
        'text': text,
        'lang': '{}-{}'.format(lang1, lang2),
        'format': 'plain'
    }
    response = requests.get(url, params)
    json = response.json()
    return json['text'][0]


if __name__ == '__main__':
    app.run()
