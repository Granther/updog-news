# import configparser
# import os

# class Config():
#     def __init__(self):
#         self.config = configparser.ConfigParser()
#         self.config.read('config.conf')

#         # Config does not exist yet
#         if not self.config.sections(): 
#             self.create_config()
#             print("Created config")
        
#         self.def_author = self.config['Defaults']['author']
#         self.def_days_old = self.config['Defaults']['days_old']
#         self.def_tag = self.config['Defaults']['tag']
#         self.max_tokens = self.config['Defaults']['max_tokens']

#     def create_config(self):    
#         self.config['Defaults'] = {"author": "Julia Garner",
#                                    "days_old": "0",
#                                    "tag": "Lifestyle",
#                                    'max_tokens': 3000}
        
#         with open('config.conf', 'w') as configfile:
#             self.config.write(configfile)

# if __name__ == "__main__":
#     conf = Config()

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'glorp')
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_URI = 'sqlite:///development.db'

class ProductionConfig(Config):
    DEBUG = False
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///production.db')

