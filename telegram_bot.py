import telebot
from telebot import types
import requests
import random
import logging
from wordfreq import top_n_list
from config import TOKEN_TELEGRAM, TOKEN_YANDEX
from base_methods import Database

bot = telebot.TeleBot(TOKEN_TELEGRAM)

YANDEX_API_URL = 'https://dictionary.yandex.net/api/v1/dicservice.json/lookup'


russian_words = top_n_list('ru', 500)
correct_answer = {}
correct_answers_count = {}


next_button = types.KeyboardButton("Старт/Далее ➡️")
add_to_favorites_button = types.KeyboardButton("Добавить в избранное 👍")
hide_word_button = types.KeyboardButton("Слово в ЧС 💩")
favorites_button = types.KeyboardButton("Избранное ❤️")

logging.basicConfig(level=logging.ERROR)


def translate_word(word, lang_from='ru', lang_to='en'):
    params = {
        'key': TOKEN_YANDEX,
        'lang': f'{lang_from}-{lang_to}',
        'text': word
    }
    try:
        response = requests.get(YANDEX_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        translations = data.get('def', [])
        if translations:
            trans_word = translations[0].get('tr', [{}])[0].get('text', '')
            return trans_word
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при запросе перевода: {e}")
    return None


def generate_word_buttons(user_id=None):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    db = Database()

    while True:
        russian_word = random.choice(russian_words)


        if len(russian_word) > 2 and (user_id and not db.check_hidden_word_for_user(user_id, russian_word) or not user_id and not db.check_hidden_word(russian_word)):
            break

    target_word = translate_word(russian_word)

    if not target_word:

        return generate_word_buttons(user_id)

    other_words = [translate_word(word) for word in random.sample(russian_words, 3) if len(word) > 2]
    other_words = [word for word in other_words if word and word != target_word]

    while len(other_words) < 3:
        additional_word = translate_word(random.choice([w for w in russian_words if len(w) > 2]))
        if additional_word and additional_word not in other_words and additional_word != target_word:
            other_words.append(additional_word)

    buttons = []
    for word in other_words:
        button = types.KeyboardButton(word)
        buttons.append(button)

    buttons.append(types.KeyboardButton(target_word))

    markup.add(*buttons)


    control_buttons = [
        next_button,
        add_to_favorites_button,
        hide_word_button,
        favorites_button
    ]
    markup.add(*control_buttons)

    return markup, russian_word, target_word


def add_to_favorites(user_id, word):
    db = Database()
    user_id = db.get_user_by_chat_id(user_id)
    if user_id:
        translation = translate_word(word)
        if translation:
            db.add_to_favorites(user_id, word, translation)
            bot.send_message(user_id, f'Слово "{word}" добавлено в Избранное ')
        else:
            bot.send_message(user_id, f'Ошибка при переводе слова "{word}".')
    else:
        bot.send_message(user_id, 'Ошибка: пользователь не найден.')


def hide_word(user_id, russian_word):
    db = Database()
    user_id = db.get_user_by_chat_id(user_id)
    if user_id:
        db.add_to_hidden_words(user_id, russian_word)
        bot.send_message(user_id, f'Слово "{russian_word}" добавлено в ЧС.')
    else:
        print(user_id, 'Ошибка: пользователь не найден.')



def show_favorites(message):
    db = Database()
    user_id = db.get_user_by_chat_id(message.chat.id)

    if user_id:
        favorites = db.get_favorites(user_id)
        if favorites:
            response = ''
            for word, translation in favorites:
                response += f'{word} - {translation}\n'
            bot.send_message(message.chat.id, f'Ваши избранные слова:\n{response}')
        else:
            bot.send_message(message.chat.id, 'У вас пока нет избранных слов.')
    else:
        bot.send_message(message.chat.id, 'Ошибка: пользователь не найден.')


@bot.message_handler(commands=['старт', 'start'])
def start_bot(message):
    db = Database()
    db.add_user(message.chat.id)

    markup, russian_word, target_word = generate_word_buttons(message.chat.id)

    correct_answer[message.chat.id] = {
        'russian_word': russian_word,
        'target_word': target_word
    }

    bot.send_message(message.chat.id, f'Cлово "{russian_word}"', reply_markup=markup)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    correct_translation = correct_answer.get(message.chat.id, {}).get('target_word')
    russian_word = correct_answer.get(message.chat.id, {}).get('russian_word')

    if message.text == correct_translation:

        if message.chat.id not in correct_answers_count:
            correct_answers_count[message.chat.id] = 0
        correct_answers_count[message.chat.id] += 1

        bot.send_message(message.chat.id, 'Верно!')


        if correct_answers_count[message.chat.id] % 5 == 0:
            bot.send_message(message.chat.id, f'Вы отлично справляетесь, правильно перевели {correct_answers_count[message.chat.id]} слов!')
            bot.send_message(message.chat.id, f'🎉')

        markup, russian_word, target_word = generate_word_buttons(message.chat.id)
        correct_answer[message.chat.id] = {
            'russian_word': russian_word,
            'target_word': target_word
        }
        bot.send_message(message.chat.id, f'Cлово "{russian_word}"', reply_markup=markup)
    elif message.text == "Старт/Далее ➡️":
        markup, russian_word, target_word = generate_word_buttons(message.chat.id)
        correct_answer[message.chat.id] = {
            'russian_word': russian_word,
            'target_word': target_word
        }
        bot.send_message(message.chat.id, f'Cлово "{russian_word}"', reply_markup=markup)
    elif message.text == "Добавить в избранное 👍":
        current_russian_word = russian_word
        add_to_favorites(message.chat.id, current_russian_word)
        markup, russian_word, target_word = generate_word_buttons(message.chat.id)
        correct_answer[message.chat.id] = {
            'russian_word': russian_word,
            'target_word': target_word
        }
        bot.send_message(message.chat.id, f'Cлово "{russian_word}"', reply_markup=markup)

    elif message.text == "Слово в ЧС 💩":
        current_russian_word = russian_word
        hide_word(message.chat.id, current_russian_word)
        markup, russian_word, target_word = generate_word_buttons(message.chat.id)
        correct_answer[message.chat.id] = {
            'russian_word': russian_word,
            'target_word': target_word
        }
        bot.send_message(message.chat.id, f'Cлово "{russian_word}"', reply_markup=markup)

    elif message.text == "Избранное ❤️":
        show_favorites(message)
        markup, russian_word, target_word = generate_word_buttons(message.chat.id)
        correct_answer[message.chat.id] = {
            'russian_word': russian_word,
            'target_word': target_word
        }
        bot.send_message(message.chat.id, f'Cлово "{russian_word}"', reply_markup=markup)

    else:
        bot.send_message(message.chat.id, 'Неверно')


if __name__ == '__main__':
    print('Bot is running')
    bot.polling()
