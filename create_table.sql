CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER UNIQUE NOT NULL
);


CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(chat_id),
    word TEXT NOT NULL,
    translation text NOT NULL
);


CREATE TABLE IF NOT EXISTS hidden_words (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(chat_id),
    word TEXT NOT NULL