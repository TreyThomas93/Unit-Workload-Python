from pymongo import MongoClient
from assets.env import uri

class mongoDatabase():

    def __init__(self):
        connected = self.connect()
        if connected:
            self.db = self.client["test"]
            self.liveWorkload = self.db["liveWorkload"]
            self.historicWorkload = self.db["historicWorkload"]
            self.system = self.db["System"]
            self.hourlyCounts = self.db["hourlyCounts"]

    def connect(self):
        try:
            self.client = MongoClient(uri)
            print("Connected To Mongo")
            return True
        except Exception as e:
            print(f"Failed To Connect To Mongo - {e}")
            return False