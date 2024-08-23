DROP TABLE IF EXISTS reporters;
DROP TABLE IF EXISTS stories;
DROP TABLE IF EXISTS authors;
DROP TABLE IF EXISTS posts;

CREATE TABLE reporters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL,
    bio TEXT,
    personality TEXT NOT NULL,
    username TEXT NOT NULL
);

CREATE TABLE stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    daysold TEXT NOT NULL,
    tags TEXT NOT NULL,
    uuid TEXT NOT NULL,
    trashed INT NOT NULL,
    archived INT NOT NULL,
    reportername TEXT NOT NULL,
    reporterid TEXT NOT NULL,
    FOREIGN KEY(reporterid) REFERENCES reporters(id)
);