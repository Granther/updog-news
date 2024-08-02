import configparser
import os

class Config():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.conf')

        # Config does not exist yet
        if not self.config.sections(): 
            self.create_config()
            print("Created config")
        
        self.add_sources = self.config['General']['add_sources']

    def create_config(self):    
        self.config['General'] = {'add_sources': False}
        
        with open('config.conf', 'w') as configfile:
            self.config.write(configfile)

if __name__ == "__main__":
    conf = Config()