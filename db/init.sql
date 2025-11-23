CREATE TABLE users (
  id SERIAL PRIMARY KEY UNIQUE NOT NULL,
  username TEXT UNIQUE NOT NULL,
  stream_token TEXT NOT NULL
);
CREATE UNIQUE INDEX id ON users (id);
CREATE UNIQUE INDEX username ON users (username);
INSERT INTO users (username, stream_token) VALUES ('streamer', 'token');
