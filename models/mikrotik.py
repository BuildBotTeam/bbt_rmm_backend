from pydantic import ConfigDict

from controllers.mongo_controller import MongoDBModel


class MikrotikRouter(MongoDBModel):
    name: str
    ip: str
    username: str
    password: str
    port: int = 8728
    favorite: bool

    class Meta:
        collection_name = 'mikrotik_routers'


def to_sneak(string: str) -> str:
    return string.replace('-', '_')


class Script(MongoDBModel):
    model_config = ConfigDict(alias_generator=to_sneak)
    name: str
    owner: str
    policy: str
    dont_require_permissions: str
    run_count: int
    source: str
    invalid: str
