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
        self.documents_path = self.config['General']['documents_path']
        self.trash_path = self.config['General']['trash_path']
        self.archive_path = self.config['General']['archived_path']
        self.def_author = self.config['Defaults']['author']
        self.def_days_old = self.config['Defaults']['days_old']
        self.def_tag = self.config['Defaults']['tag']
        self.max_tokens = self.config['Defaults']['max_tokens']

    def create_config(self):    
        self.config['General'] = {'add_sources': False,
                                  'documents_path': 'documents/',
                                  'trash_path': 'documents/trash/',
                                  'archived_path': 'documents/archived/',
                                  'max_tokens': 3000}
        self.config['Defaults'] = {"author": "Julia Garner",
                                   "days_old": "0",
                                   "tag": "Lifestyle"}
        
        with open('config.conf', 'w') as configfile:
            self.config.write(configfile)

if __name__ == "__main__":
    conf = Config()

