from groq import Groq
import xml.etree.ElementTree as ET
import shortuuid
import sqlite3
import os

class ReportersSQL():
    def __init__(self):
        self.connection = sqlite3.connect('database.db', check_same_thread=False)
        #self.connection.row_factory = lambda cursor, row: row[0]

    def parse_reporters(self):
        # This needs to be redone a little, I'm upset at how im unpacking
        query = 'SELECT id, name, bio FROM reporters'

        response = self.connection.cursor().execute(query).fetchall()
        reporters = list()

        for res in response:
            reporter = {
                "name": res[1],
                "bio": res[2],
                "id": res[0]
            }
            reporters.append(reporter)
        return reporters

    def create_reporter(self, name: str=None, bio: str=None, personality: str=None):
        if name == None or personality == None:
            return "Error creating reporter"
        
        cursor = self.connection.cursor()
        query = f"""INSERT INTO reporters (name, bio, personality, uuid) VALUES ('{name}', '{bio.replace("'", "''")}', '{personality.replace("'", "''")}', '{str(shortuuid.uuid())}')"""
        cursor.execute(query)
        self.connection.commit() 
    
    def send_query(self, query):
        return self.connection.cursor().execute(query).fetchall()