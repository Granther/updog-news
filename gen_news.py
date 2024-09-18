from groq import Groq
import xml.etree.ElementTree as ET
from reporters import ReportersSQL
import shortuuid
import sqlite3
import os

class GenerateNewsSQL():
    def __init__(self):
        self.connection = sqlite3.connect('database.db', check_same_thread=False)
        self.repSQL = ReportersSQL()

    def parse_news(self, index=True, all=False):
        if all:
            query = """SELECT title, content, daysold, tags, uuid, reporterid, reportername 
                    FROM stories
                    ORDER BY created;"""
        elif index:
            # Select all stories not trashed or archived
            query = """SELECT title, content, daysold, tags, uuid, reporterid, reportername 
                    FROM stories
                    WHERE trashed = FALSE AND archived = FALSE
                    ORDER BY created;"""
        elif not index:
            # Select archived
            query = """SELECT title, content, daysold, tags, uuid, reporterid, reportername 
                    FROM stories
                    WHERE archived = TRUE
                    ORDER BY created"""

        response = self.connection.cursor().execute(query).fetchall()
        stories = list()

        for res in response:
            story = {
                "title": res[0],
                "content": res[1],
                "days": res[2],
                "tags": res[3],
                "uuid": res[4],
                "reporterid": res[5],
                "reportername": res[6],
            }
            stories.append(story)
        return stories
    
    def parse_news_reporter(self, username: str):
        query = f"""SELECT title, content, daysold, tags, uuid, reporterid, reportername 
                FROM stories
                WHERE reporterid = {self.get_reporter_id(username)}
                ORDER BY created;"""

        response = self.connection.cursor().execute(query).fetchall()
        stories = list()

        for res in response:
            story = {
                "title": res[0],
                "content": res[1],
                "days": res[2],
                "tags": res[3],
                "uuid": res[4],
                "reporterid": res[5],
                "reportername": res[6],
            }
            stories.append(story)
        return stories
    
    def get_reporter_id(self, name: str):
        query = f"""SELECT id FROM reporters WHERE username = '{self.repSQL.make_username(name)}';"""
        x = self.send_query(query)
        return int(x[0][0])

    def create_story(self, title: str, content: str, days: str="0", reporter: str = None, tags: str = None, archived: int = 0, trashed: int = 0):
        cursor = self.connection.cursor()

        if self.repSQL.reporter_exists(reporter):
            reporterid = self.get_reporter_id(reporter)
        else:
            reporterid = 1000

        query = f"""INSERT INTO stories (title, content, daysold, uuid, tags, reportername, reporterid, archived, trashed) VALUES ('{title}', '{content.replace("'", "''")}', '{days}', '{str(shortuuid.uuid())}', '{tags}', '{reporter}', {reporterid}, '{archived}', '{trashed}')"""
        res = cursor.execute(query)
        self.connection.commit() 

        return res

    def _is_archived(self, uuid):
        query = f"SELECT archived FROM stories WHERE uuid = '{uuid}'"
        response = self.connection.cursor().execute(query).fetchall()[0]

        return not bool(response)
    
    def send_query(self, query):
        return self.connection.cursor().execute(query).fetchall()

    def toggle_archive(self, uuid):
        if self._is_archived(uuid):
            query = f"UPDATE stories SET archived = FALSE, trashed = FALSE WHERE uuid = '{uuid}'"
        else:
            query = f"UPDATE stories SET archived = TRUE, trashed = FALSE WHERE uuid = '{uuid}'"

        response = self.send_query(query)

    def trash(self, uuid):
        query = f"UPDATE stories SET trashed = TRUE WHERE uuid = '{uuid}'"

        response = self.connection.cursor().execute(query).fetchall()
        if len(response) > 0:
            return 1
        elif len(response) >= 1:
            return 0