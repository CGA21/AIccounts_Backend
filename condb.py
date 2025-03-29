from pymongo import MongoClient
from datetime import datetime
import configparser

class DB:
    def __init__(self):
        # Connect to MongoDB (update URI if needed)
        config = configparser.ConfigParser()
        config.read('config.ini')
        client = MongoClient(config['Mongo']['db_url'])
        db = client["HackDay"]
        self.collection = db["invoices"]

    def insert_invoice(self,data):
        if self.collection.insert_one(data):
            return True
        else:
            return False

