CREATE TABLE IF NOT EXISTS questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_text TEXT NOT NULL,
    qr_code_link TEXT
);

CREATE TABLE IF NOT EXISTS responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    question_id INTEGER NOT NULL,
    response_text TEXT NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions (question_id)
);
