from pymongo import MongoClient
from assets.env import uri, client
from termcolor import colored

class mongoDatabase():

    def __init__(self):
        connected = self.connect()
        
        if connected:
            self.db = self.client[client]
            self.liveWorkload = self.db["liveWorkload"]
            self.system = self.db["system"]

    def connect(self):
        try:
            self.client = MongoClient(uri)
            print(colored("Connected To Mongo", "green"))
            return True
        except Exception as e:
            print(colored(f"Failed To Connect To Mongo - {e}", "red"))
            return False