import asyncio
import ssl
from datetime import datetime
from typing import Union

import asyncssh
from pydantic import ConfigDict, BaseModel, Field
from controllers.mongo_controller import MongoDBModel, db
from bson import ObjectId as BsonObjectId

from views.ws_app import manager


class MikrotikSNMPLogs(BaseModel):
    time: str
    bytes_in: Union[str, None] = None
    bytes_out: Union[str, None] = None
    online: bool = True
    version_os: Union[str, None] = None


class MikrotikLogs(BaseModel):
    time: str
    topics: str
    message: str

    @classmethod
    def convert_log(cls, logs):
        result_list = []
        for log in logs:
            res = log.strip().split()
            if not res:
                continue
            if len(res[0]) == 5:
                res[0] += ' ' + res.pop(1)
            time = ''.join(res[:1])
            topics = ''.join(res[1:2])
            message = ' '.join(res[2:])
            if 'via ssh' in message:
                continue
            if len(time) == 8:
                now = datetime.now()
                day = str(now.day).rjust(2, '0')
                month = str(now.month).rjust(2, '0')
                time = f'{month}-{day} {time}'
            result_list.append(cls(time=time, topics=topics, message=message))
        return result_list

    @classmethod
    def add_newest_logs(cls, last_log, logs):
        result_list = []
        logs = cls.convert_log(logs)
        if last_log:
            for log in logs:
                if 'via api' in log.message:
                    continue
                if log.time > last_log.time or (log.time == last_log.time and last_log.message != log.message):
                    result_list.append(log)
        else:
            result_list = logs
        result_list.reverse()
        return result_list


class MikrotikRouter(MongoDBModel):
    name: str = ''
    host: str
    username: str
    password: str
    version_os: Union[str, None] = None
    logs: list[MikrotikLogs] = []
    status_log: list[MikrotikSNMPLogs] = []
    user_id: Union[str, None] = None
    is_online: bool = True

    class Meta:
        collection_name = 'mikrotik_routers'

    def add_logs(self, logs: list):
        if logs and isinstance(logs, list):
            last_log = self.logs[0] if self.logs else None
            self.logs += MikrotikLogs.add_newest_logs(last_log, logs)
            self.save()

    async def get_logs(self):
        try:
            async with asyncssh.connect(self.host, username=self.username, password=self.password,
                                        known_hosts=None) as conn:
                result = await conn.run('log print')
                self.add_logs(result.stdout.replace('\r', '').split('\n'))
        except Exception as e:
            print(e)

    @classmethod
    async def ping(cls, ids: list[str], host: str, count: int = 1, **kwargs):
        command = f'ping {host} count={count}'
        await cls.try_send_command(ids, command)

    @classmethod
    async def send_script(cls, ids: list[str], script_name: str, source: str, **kwargs):
        command = f'system/script/ add name={script_name} source="{source}"; system/script/ run {script_name}'
        await cls.try_send_command(ids, command)

    @classmethod
    async def get_scripts(cls, ids: list[str], **kwargs):
        command = f'system/script/ print'
        await cls.try_send_command(ids, command)

    @classmethod
    async def remove_script(cls, ids: list[str], script_name: str, **kwargs):
        command = f'system/script/ remove {script_name}'
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
