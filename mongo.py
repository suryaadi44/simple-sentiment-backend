import pymongo
from decouple import config

mongo_client = pymongo.MongoClient(config("DATABASE_URL"))
db = mongo_client[config("DATABASE_NAME")]

collist = db.list_collection_names()
if "predictions" not in collist:
    db.create_collection("predictions")
predictions_collection = db["predictions"]

if "users" not in collist:
    db.create_collection("users")
users_collection = db["users"]