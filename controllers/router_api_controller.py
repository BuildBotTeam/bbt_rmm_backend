from routeros_api.api import RouterOsApi, RouterOsApiPool
import ssl

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


api = connect('admin', 'admin')
log = api.get_resource('/log').get()
for l in log:
    print(l)
