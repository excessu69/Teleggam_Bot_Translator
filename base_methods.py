import psycopg2
from psycopg2 import sql
import logging
from db_config import NAME, USER, PASSWORD, HOST, PORT

class Database:
    def __init__(self):
        self.conn = self.connect()

    def connect(self):
        try:
            logging.info(f"Подключение к базе данных с параметрами: dbname={NAME}, user={USER}, password=****, host={HOST}, port={PORT}")
            conn = psycopg2.connect(
                dbname=NAME,
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
            )
            return conn
        except psycopg2.Error as e:
            logging.error(f"Ошибка подключения к PostgreSQL: {e}")
            return None

    def add_user(self, chat_id):
        if self.conn:
            try:
                logging.info(f"Добавление пользователя с chat_id: {chat_id}")
                with self.conn.cursor() as cur:
                    cur.execute(
                        sql.SQL("INSERT INTO users (chat_id) VALUES (%s) ON CONFLICT DO NOTHING"),
                        (chat_id,)
                    )
                    self.conn.commit()
                    logging.info(f"Добавлен новый пользователь с chat_id {chat_id}")
                    print(chat_id)
            except psycopg2.Error as e:
                logging.error(f"Ошибка при добавлении нового пользователя: {e}")

    def get_user_by_chat_id(self, chat_id):
        if self.conn:
            try:
                logging.info(f"Получение пользователя с chat_id: {chat_id}")
                with self.conn.cursor() as cur:
                    cur.execute(
                        sql.SQL("SELECT chat_id FROM users WHERE chat_id = %s"),
                        (chat_id,)
                    )
                    user_chat_id = cur.fetchone()
                    if user_chat_id:
                        return str(user_chat_id[0])
                    return None
            except psycopg2.Error as e:
                logging.error(f"Ошибка при чтении пользователя по chat_id: {e}")

    def add_to_favorites(self, user_id, word, translation):
        if self.conn:
            try:
                user_id = int(user_id)
                logging.info(f"Добавление слова '{word}' в избранное для пользователя с user_id: {user_id}")
                with self.conn.cursor() as cur:
                    cur.execute(
                        sql.SQL("INSERT INTO favorites (user_id, word, translation) VALUES (%s, %s, %s)"),
                        (user_id, word, translation)
                    )
                    self.conn.commit()
                    logging.info(
                        f"Слово '{word}' добавлено в избранное для пользователя {user_id} с переводом '{translation}'")
            except (psycopg2.Error, ValueError) as e:
                logging.error(f"Ошибка при добавлении слова в избранное: {e}")
    def add_to_hidden_words(self, user_id, word):
        if self.conn:
            try:
                logging.info(f"Добавление слова в скрытые для пользователя с user_id: {user_id}, слово: {word}")
                with self.conn.cursor() as cur:
                    cur.execute(
                        sql.SQL("INSERT INTO hidden_words (user_id, word) VALUES (%s, %s)"),
                        (user_id, word)
                    )
                    self.conn.commit()
                    logging.info(f"Слово '{word}' добавлено в скрытые для пользователя {user_id}")
            except psycopg2.Error as e:
                logging.error(f"Ошибка при добавлении слова в скрытые: {e}")

    def get_favorites(self, user_id):
        if self.conn:
            try:
                logging.info(f"Получение избранных слов для пользователя с user_id: {user_id}")
                with self.conn.cursor() as cur:
                    cur.execute(
                        sql.SQL("SELECT word, translation FROM favorites WHERE user_id = %s"),
                        (user_id,)
                    )
                    favorites = cur.fetchall()
                    return favorites
            except psycopg2.Error as e:
                logging.error(f"Ошибка при чтении избранных слов: {e}")

    def get_hidden_words(self, user_id):
        if self.conn:
            try:
                logging.info(f"Получение скрытых слов для пользователя с user_id: {user_id}")
                with self.conn.cursor() as cur:
                    cur.execute(
                        sql.SQL("SELECT word FROM hidden_words WHERE user_id = %s"),
                        (user_id,)
                    )
                    hidden_words = cur.fetchall()
                    return [word[0] for word in hidden_words]
            except psycopg2.Error as e:
                logging.error(f"Ошибка при чтении скрытых слов: {e}")

    def check_hidden_word_for_user(self, user_id, russian_word):
        if self.conn:
            try:
                with self.conn.cursor() as cur:
                    cur.execute(
                        sql.SQL("SELECT EXISTS(SELECT 1 FROM hidden_words WHERE user_id = %s AND word = %s)"),
                        (user_id, russian_word)
                    )
                    exists = cur.fetchone()[0]
                    return exists
            except psycopg2.Error as e:
                logging.error(f"Ошибка при проверке скрытого слова для пользователя: {e}")
        return False


    def close_connection(self):
        if self.conn:
            self.conn.close()
            logging.info("Соединение с базой данных закрыто")
