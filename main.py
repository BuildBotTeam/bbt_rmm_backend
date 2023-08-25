import routeros_api
from routeros_api.api import RouterOsApi
from pysnmp.hlapi import *

IP_MIKROTIK = '192.168.252.134'
OIDS = {
    '1.3.6.1.2.1.31.1.1.1.6.1': 'bytes-in',
    '1.3.6.1.2.1.31.1.1.1.10.1': 'bytes-out',
}


class Script:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.owner = kwargs.get('owner')
        self.policy = kwargs.get('policy')
        self.dont_require_permissions = kwargs.get('dont-require-permissions')
        self.run_count = kwargs.get('run-count')
        self.source = kwargs.get('source')
        self.invalid = kwargs.get('invalid')

    def __str__(self):
        return f"{self.__dict__}"


def connect(username: str, password: str) -> RouterOsApi:
    connection = routeros_api.RouterOsApiPool(IP_MIKROTIK, username=username, password=password, port=8728,
                                              use_ssl=False,
                                              ssl_verify=True,
                                              plaintext_login=True,
                                              ssl_verify_hostname=True, )
    api = connection.get_api()
    return api


def get_oid_data():
    iterator = getCmd(
        SnmpEngine(),
        CommunityData('public', mpModel=1),
        UdpTransportTarget((IP_MIKROTIK, 161)),
        ContextData(),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.31.1.1.1.6.1')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.31.1.1.1.10.1')),
        lookupMib=False,
        lexicographicMode=False
    )

    error_indication, error_status, error_index, var_binds = next(iterator)
    if error_indication:
        print(error_indication)
    elif error_status:
        print('%s at %s' % (error_status.prettyPrint(), error_index and var_binds[int(error_index) - 1][0] or '?'))
    else:
        for var_bind in var_binds:
            oid, data = [x.prettyPrint() for x in var_bind]
            print(' = '.join([OIDS[oid], data]))


if __name__ == '__main__':
    get_oid_data()
    # api = connect('admin', 'admin')
    # list = api.get_resource('/system/script')
    # for l in list.get():
    #     s = Script(**l)
    #     print(s)
