from routeros_api.api import RouterOsApi, RouterOsApiPool

IP_MIKROTIK = '192.168.252.134'


def connect(username: str, password: str) -> RouterOsApi:
    connection = RouterOsApiPool(IP_MIKROTIK, username=username, password=password, port=8728,
                                 use_ssl=False,
                                 ssl_verify=True,
                                 plaintext_login=True,
                                 ssl_verify_hostname=True, )
    api = connection.get_api()
    return api
