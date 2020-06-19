from assets.database import mongoDatabase
from assets.currentDatetime import current_dateTime
from assets.errorHandler import checkError

from workload.live import liveWorkloadHandler
from fakeData import GenerateFakeData

import platform
import os
import time
from pprint import pprint
import threading
from termcolor import colored

class Master():

    def __init__(self):

        self.mongo = mongoDatabase()
        self.liveWorkload = self.mongo.liveWorkload

        self.fakeData = GenerateFakeData(self.liveWorkload)

        self.liveWorkloadHandler = liveWorkloadHandler(self.liveWorkload)

    @checkError
    def listen(self):
        start = time.perf_counter()
        print(colored("\n[GENERATING FAKE DATA]", "green"))
        print(colored("~~~~~~~~~~~~~~~~~~~~~~~~~~~~", "blue"))
        self.fakeData.generateData()
        Data = self.fakeData.Data
        print(colored("\n[HANDLING LIVE WORKLOAD]", "green"))
        print(colored("~~~~~~~~~~~~~~~~~~~~~~~~~~~~", "blue"))
        self.liveWorkloadHandler(Data)

        end = time.perf_counter()

        print(colored(
            f"\n--> Cycle Complete - {current_dateTime()} - Took {round(end-start, 2)} second(s)\n", "yellow"))

if __name__ == "__main__":
    master = Master()
    master.listen()