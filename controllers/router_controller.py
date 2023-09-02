import asyncio, asyncssh
from datetime import datetime

from models.mikrotik import MikrotikRouter, MikrotikSNMPLogs
from pysnmp.hlapi.asyncio import *

OIDS = {
    '1.3.6.1.2.1.31.1.1.1.6.1': 'bytes-in',
    '1.3.6.1.2.1.31.1.1.1.10.1': 'bytes-out',
}


# region SNMP

async def get_oid_data(router: MikrotikRouter, counter):
    error_indication, error_status, error_index, var_binds = await getCmd(
        SnmpEngine(),
        CommunityData('public', mpModel=1),
        UdpTransportTarget((router.host, 161)),
        ContextData(),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.31.1.1.1.6.1')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.31.1.1.1.10.1')),
        lookupMib=False,
        lexicographicMode=False
    )

    result = {'time': datetime.now().strftime('MM-DD HH:mm:ss')}
    if error_indication:
        print(error_indication)
        return None

    if error_status:
        print('%s at %s' % (error_status.prettyPrint(), error_index and var_binds[int(error_index) - 1][0] or '?'))
        return None

    for var_bind in var_binds:
        oid, data = [x.prettyPrint() for x in var_bind]
        result[OIDS[oid]] = data
    print(MikrotikSNMPLogs(**result))


async def get_status():
    print('start_status')
    counter = 0
    routers: list[MikrotikRouter] = MikrotikRouter.filter()
    tasks = (get_oid_data(router, counter) for router in routers)
    await asyncio.gather(*tasks)
    await asyncio.sleep(5)


# endregion

# region SSH

async def get_logs():
    while True:
        print('start logs')
        routers: list[MikrotikRouter] = MikrotikRouter.filter()
        tasks = (router.get_logs() for router in routers)
        await asyncio.gather(*tasks)
        await asyncio.sleep(20)

# endregion
