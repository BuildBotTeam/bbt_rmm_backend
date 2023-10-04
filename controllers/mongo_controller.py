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
    id: Union[ObjectId, None] = None

    def __init__(self, **kwargs):
        if '_id' in kwargs:
            kwargs['id'] = kwargs.pop('_id')
        super().__init__(**kwargs)

    @classmethod
    def get(cls, id: Union[str, None] = None, **kwargs):
        if id:
            data = db[cls.Meta.collection_name].find_one({'_id': BsonObjectId(id), **kwargs})
        else:
            print(kwargs)
            data = db[cls.Meta.collection_name].find_one(kwargs)
        return cls(**data) if data else None

    @classmethod
    def filter(cls, ids: Union[list, None] = None,  **kwargs):
        if isinstance(ids, list):
            data_list = db[cls.Meta.collection_name].find({'_id': {'$in': [BsonObjectId(m) for m in ids]}})
        else:
            data_list = db[cls.Meta.collection_name].find(kwargs)
        return [cls(**data) for data in data_list]

    @classmethod
    def bulk_create(cls, data: list):
        result = db[cls.Meta.collection_name].insert_many(data)
        return cls.filter(result.inserted_ids)

    @classmethod
    def bulk_delete(cls, ids: Union[list, None] = None):
        if not ids:
            db[cls.Meta.collection_name].delete_many({})
        else:
            db[cls.Meta.collection_name].delete_many({'_id': {'$in': [BsonObjectId(v) for v in ids]}})

    def create(self):
        document = self.model_dump()
        try:
            result = db[self.__class__.Meta.collection_name].insert_one(document)
            return self.__class__.get(id=result.inserted_id)
        except Exception as e:
            print(e)
            return None

    def save(self):
        document = self.model_dump()
        document.pop('id')
        try:
            data = db[self.__class__.Meta.collection_name].update_one({"_id": BsonObjectId(self.id)},
                                                                      {"$set": document})
            return self.__class__.get(id=data.upserted_id)
        except Exception as e:
            print(e)
            return None

    def delete(self):
        try:
            db[self.__class__.Meta.collection_name].delete_one({"_id": BsonObjectId(self.id)})
            return True
        except Exception as e:
            print(e)
            return False
