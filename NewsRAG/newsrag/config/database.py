
#### get rid of the logger

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

#### MAYBE????
import os
from dotenv import load_dotenv
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
##############################################

class MongoDatabaseConnector:
    _instance: MongoClient | None = None

    def __new__(cls, *args, **kwargs) -> MongoClient:
        if cls._instance is None:
            try:
                cls._instance = MongoClient(MONGO_URI)
                #settings.DATABASE_HOST
            except ConnectionFailure as e:
                # logger.error(f"Couldn't connect to the database: {str(e)}")
                print(f"Connection Failure: {str(e)}")
                raise
        print("Connection enstablished")
        # logger.info(
        #     f"Connection to database with uri: {settings.DATABASE_HOST} successful"
        # )
        return cls._instance

    def close(self):
        if self._instance:
            self._instance.close()
            # logger.info("Connected to database has been closed.")


# connection = MongoDatabaseConnector()