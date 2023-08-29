from pymongo import MongoClient
from models.settings import settings
from bson import ObjectId as BsonObjectId
from pydantic import BaseModel, Field
from typing import Union

client = MongoClient(
    f"mongodb://{settings.MONGO_INITDB_ROOT_USERNAME}:{settings.MONGO_INITDB_ROOT_PASSWORD}@mongo:27017/{settings.MONGO_INITDB_DATABASE}")
db = client[settings.MONGO_INITDB_DATABASE]


class ObjectId(BsonObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, some):
        return str(v)


class MongoDBModel(BaseModel):
    id: Union[ObjectId, None] = Field(default=None, alias='_id')

    @classmethod
    def get(cls, id: Union[str, None]):
        if id:
            data = db[cls.Meta.collection_name].find_one({'_id': BsonObjectId(id)})
            if data:
                return cls(**data)
        return None

    @classmethod
    def filter(cls, **kwargs):
        users = db[cls.Meta.collection_name].find(**kwargs)
        return [cls(**user) for user in users]

    def create(self):
        document = self.model_dump()
        try:
            result = db['users'].insert_one(document)
            return self.__class__.get(id=result.inserted_id)
        except Exception:
            return None

    def save(self):
        document = self.model_dump()
        try:
            user = db['users'].update_one({"_id": BsonObjectId(self.id)}, {"$set": document})
            return self.__class__.get(id=user.upserted_id)
        except Exception as e:
            print(e)
            return None
