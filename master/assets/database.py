from pymongo import MongoClient
from assets.env import uri
from termcolor import colored

class mongoDatabase():

    def __init__(self):
        connected = self.connect()
        
        testing = False
        if testing:
            client = "test"
        else:
            client = "EMSAEastern"

        if connected:
            self.db = self.client[client]
            self.liveWorkload = self.db["liveWorkload"]
            self.historicWorkload = self.db["historicWorkload"]
            self.system = self.db["System"]
            self.master = self.db["Master"]

    def connect(self):
        try:
            self.client = MongoClient(uri)
            print(colored("Connected To Mongo", "green"))
            return True
        except Exception as e:
            print(colored(f"Failed To Connect To Mongo - {e}", "red"))
            return False