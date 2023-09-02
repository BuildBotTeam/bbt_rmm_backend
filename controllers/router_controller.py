import asyncio, asyncssh
from datetime import datetime

from models.mikrotik import MikrotikRouter, MikrotikSNMPLogs
from pysnmp.hlapi.asyncio import *

from views.ws_app import manager

OIDS = {
    '1.3.6.1.2.1.31.1.1.1.6.1': 'bytes_in',
    '1.3.6.1.2.1.31.1.1.1.10.1': 'bytes_out',
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

    result = {'time': datetime.now().strftime('%m-%d %H:%M:%S')}
    if error_indication and router.is_online:
        router.is_online = False
        router.save()
        await manager.broadcast(router.user_id, router.model_dump(exclude='password'))
        print('error', router.host)
        return None

    if not router.is_online:
        router.is_online = True
        router.save()
        await manager.broadcast(router.user_id, router.model_dump(exclude='password'))

    for var_bind in var_binds:
        oid, data = [x.prettyPrint() for x in var_bind]
        result[OIDS[oid]] = data
    print(MikrotikSNMPLogs(**result))


async def get_status():
    counter = 0
    while True:
        if counter == 5:
            counter = 0
        print('start_status')
        routers: list[MikrotikRouter] = MikrotikRouter.filter()
        tasks = (get_oid_data(router, counter) for router in routers)
        await asyncio.gather(*tasks)
        print('end_status', counter)
        counter += 1
        await asyncio.sleep(5)


# endregion

# region SSH

async def get_logs():
    while True:
        print('start gather logs')
        routers: list[MikrotikRouter] = MikrotikRouter.filter()
        tasks = (router.get_logs() for router in routers)
        await asyncio.gather(*tasks)
        print('end gather logs')
        await asyncio.sleep(20)

# endregion
