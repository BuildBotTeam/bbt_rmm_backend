from routeros_api.api import RouterOsApi, RouterOsApiPool
import ssl
from datetime import datetime

from models.mikrotik import MikrotikLogs

IP_MIKROTIK = '192.168.252.134'


def connect(username: str, password: str) -> RouterOsApi:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    ssl_context.set_ciphers("ADH:ALL:@SECLEVEL=0")
    connection = RouterOsApiPool(IP_MIKROTIK, username=username, password=password,
                                 use_ssl=True,
                                 ssl_verify=True,
                                 plaintext_login=True,
                                 ssl_verify_hostname=True, ssl_context=ssl_context)
    api = connection.get_api()
    return api


last_log = {'id': '*4E', 'time': '08-31 07:08:09', 'topics': 'system,info,account',
            'message': 'filter rule changed by admisdsn'}

api = connect('admin', 'admin')
log = api.get_resource('/log').get()


def convert_log(logs, router_id):
    result_list = []
    for log in logs:
        log.pop('id')
        log['router_id'] = router_id
        if len(log['time']) == 8:
            now = datetime.now()
            day = str(now.day).rjust(2, '0')
            month = str(now.month).rjust(2, '0')
            log['time'] = f'{month}-{day} {log["time"]}'
        result_list.append(log)
    return result_list


for i in range(len(log)):
    if len(log[i]['time']) == 8:
        now = datetime.now()
        day = str(datetime.now().day).rjust(2, '0')
        month = str(datetime.now().month).rjust(2, '0')
        log[i]['time'] = f'{month}-{day} {log[i]["time"]}'
    # and int(log[i]['id'][1:], 16) > int(last_log['id'][1:], 16)
    if last_log and log[i]['time'] >= last_log['time']:
        if 'via api' in log[i]['message']:
            continue
        if last_log['message'] != log[i]['message']:
            print(log[i])
