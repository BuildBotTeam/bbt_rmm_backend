import ssl
from datetime import datetime
from typing import Union

from pydantic import ConfigDict, BaseModel
from controllers.mongo_controller import MongoDBModel, db
from routeros_api.api import RouterOsApiPool


class MikrotikLogs(BaseModel):
    time: str
    topics: str
    message: str

    @classmethod
    def convert_log(cls, logs):
        result_list = []
        for log in logs:
            res = log.strip().split()
            time = ''.join(res[:1])
            topics = ''.join(res[1:2])
            message = ' '.join(res[2:])
            if 'via ssh' in message:
                continue
            if len(time) <= 8:
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
            return result_list
        return logs


class MikrotikRouter(MongoDBModel):
    host: str
    username: str
    password: str
    logs: list[MikrotikLogs] = []
    user_id: Union[str, None] = None

    class Meta:
        collection_name = 'mikrotik_routers'

    def add_logs(self, logs: list):
        if logs and isinstance(logs, list):
            last_log = self.logs[-1] if self.logs else None
            self.logs += MikrotikLogs.add_newest_logs(last_log, logs)
            self.save()

    def connect(self):
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            ssl_context.set_ciphers("ADH:ALL:@SECLEVEL=0")
            connection = RouterOsApiPool(self.host, username=self.username, password=self.password,
                                         use_ssl=True, ssl_verify=True, plaintext_login=True,
                                         ssl_verify_hostname=True, ssl_context=ssl_context)
            return connection
        except Exception as e:
            print(e)
            return None


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
