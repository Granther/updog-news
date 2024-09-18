from groq import Groq
import xml.etree.ElementTree as ET
import shortuuid
import sqlite3
import os

class ReportersSQL():
    def __init__(self):
        self.connection = sqlite3.connect('database.db', check_same_thread=False)
        #self.connection.row_factory = lambda cursor, row: row[0]

    def parse_reporters(self, username: str = None):
        # This needs to be redone a little, I'm upset at how im unpacking
        # if username != None and 
        if username != None:
            query = f"SELECT personality, name, bio, username FROM reporters WHERE username = '{username}'"
        # Parse all
        elif username == None:
            query = 'SELECT personality, name, bio, username FROM reporters'

        response = self.connection.cursor().execute(query).fetchall()
        reporters = list()

        for res in response:
            reporter = {
                "name": res[1],
                "bio": res[2],
                "personality": res[0],
                "username": res[3],
            }
            reporters.append(reporter)
        return reporters

    def get_personality(self, name: str):
        if not self.reporter_exists(name):
            return False
        
        name = self.make_username(name)
        
        query = f"SELECT personality FROM reporters WHERE username = '{name}'"
        res = self.send_query(query)

        return res[0][0]

    def create_reporter(self, name: str=None, bio: str=None, personality: str=None):
        if self.reporter_exists(name):
            return False

        if name == None or personality == None:
            return "Error creating reporter"
        
        if bio == '':
            query = f"""INSERT INTO reporters (name, personality, username) VALUES ('{name}', '{personality.replace("'", "''")}', '{self.make_username(name)}')"""
        else:
            query = f"""INSERT INTO reporters (name, bio, personality, username) VALUES ('{name}', '{bio.replace("'", "''")}', '{personality.replace("'", "''")}', '{self.make_username(name)}')"""

        cursor = self.connection.cursor()
        res = cursor.execute(query)
        self.connection.commit() 

        return res
    
    def make_username(self, name: str):
        return name.replace(" ", "").lower()
    
    def reporter_exists(self, name) -> bool:
        name = self.make_username(name)

        query = f"""SELECT * FROM reporters WHERE username = '{name}'"""
        if len(self.send_query(query)) > 0:
            return True
        
        return False
    
    def send_query(self, query):
        return self.connection.cursor().execute(query).fetchall()