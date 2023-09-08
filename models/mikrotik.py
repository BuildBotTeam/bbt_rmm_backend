import asyncio
from datetime import datetime
from typing import Union

import asyncssh
from pydantic import ConfigDict, BaseModel
from controllers.mongo_controller import MongoDBModel
from models.settings import settings

from views.ws_app import manager


class MikrotikSNMPLogs(BaseModel):
    time: str
    bytes_in: Union[str, None] = None
    bytes_out: Union[str, None] = None
    online: bool = True
    version_os: Union[str, None] = None


class MikrotikLogs(BaseModel):
    datetime: str
    topics: str
    message: str

    @classmethod
    def convert_log(cls, log):
        res = log.strip().split()
        return cls(datetime=datetime.now().isoformat(), topics=res[0], message=' '.join(res[1:]))


class MikrotikRouter(MongoDBModel):
    name: str = ''
    host: str
    username: str
    password: str
    topics: list[str] = []
    version_os: Union[str, None] = None
    logs: list[MikrotikLogs] = []
    status_log: list[MikrotikSNMPLogs] = []
    user_id: Union[str, None] = None
    is_online: bool = True

    class Meta:
        collection_name = 'mikrotik_routers'

    def add_log(self, log: str):
        if log:
            self.logs.insert(0, MikrotikLogs.convert_log(log))
            self.save()

    @classmethod
    async def ping(cls, ids: list[str], host: str, count: int = 1, **kwargs):
        command = f'/ping {host} count={count}'
        await cls.try_send_command(ids, command)

    @classmethod
    async def send_script(cls, ids: list[str], script_name: str, source: str, **kwargs):
        source = source.replace('\"', '\\\"')
        command = f'/system/script/ add name="{script_name}" source="{source}";/system/script/ run {script_name};'
        await cls.try_send_command(ids, command)

    @classmethod
    async def get_scripts(cls, ids: list[str], **kwargs):
        command = f'/system/script/ print'
        await cls.try_send_command(ids, command)

    @classmethod
    async def remove_script(cls, ids: list[str], script_name: str, **kwargs):
        command = f'/system/script/ remove {script_name}'
        await cls.try_send_command(ids, command)

    @classmethod
    async def try_send_command(cls, ids: list[str], raw_command: str, **kwargs):
        routers: list[MikrotikRouter] = cls.filter(ids=ids)
        for router in routers:
            if router.is_online:
                asyncio.create_task(cls.send_command(router, raw_command))

    @classmethod
    async def send_command(cls, router, raw_command: str):
        async with asyncssh.connect(router.host, username=router.username, password=router.password,
                                    known_hosts=None) as conn:
            result = await conn.run(raw_command)
            await manager.broadcast(router.user_id, 'command_result',
                                    {'is_success': result.exit_status == 0,
                                     'result': f'{router.name} - {router.host}:\n{result.stdout}{"-" * 50}\n\n'})

    async def connect_to_syslog(self):
        command = f'/system/logging/action add remote={settings.HOST} name="bbtrmm" remote-port=514 target=remote;'
        for topic in self.topics:
            command += f'/system/logging add action="bbtrmm" topics={topic};'
        command += '/log error message="test message on create connection to syslog";'
        await self.send_command(router=self, raw_command=command)


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
