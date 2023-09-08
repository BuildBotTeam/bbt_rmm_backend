import asyncio, asyncssh
from datetime import datetime

from models.mikrotik import MikrotikRouter, MikrotikSNMPLogs
from pysnmp.hlapi.asyncio import *

from views.ws_app import manager

OIDS = {
    '1.3.6.1.2.1.31.1.1.1.6.1': 'bytes_in',
    '1.3.6.1.2.1.31.1.1.1.10.1': 'bytes_out',
    '1.3.6.1.2.1.47.1.1.1.1.2.65536': 'version_os',
}


# region SNMP

async def get_oid_data(router: MikrotikRouter, counter):
    error_indication, error_status, error_index, var_binds = await getCmd(
        SnmpEngine(),
        CommunityData('public', mpModel=1),
        UdpTransportTarget((router.host, 161)),
        ContextData(),
        *[ObjectType(ObjectIdentity(oid)) for oid in OIDS.keys()],
        lookupMib=False,
        lexicographicMode=False
    )

    result = {'time': datetime.now().strftime('%m-%d %H:%M:%S')}
    if error_indication:
        if router.is_online:
            router.is_online = False
            result['online'] = False
            router.status_log.append(MikrotikSNMPLogs(**result))
            router.save()
            await manager.broadcast(router.user_id, 'update_router', router.model_dump(exclude='password'))
        return None

    if not router.is_online:
        router.is_online = True
        router.save()
        await manager.broadcast(router.user_id, 'update_router', router.model_dump(exclude='password'))

    if counter == 0:
        for var_bind in var_binds:
            oid, data = [x.prettyPrint() for x in var_bind]
            result[OIDS[oid]] = data
        version_os = result.get('version_os')
        if version_os != router.version_os:
            router.version_os = version_os
            await manager.broadcast(router.user_id, 'update_router', router.model_dump(exclude='password'))
        router.status_log.append(MikrotikSNMPLogs(**result))
        router.save()


async def get_status():
    counter = 0
    while True:
        if counter == 20:
            counter = 0
        routers: list[MikrotikRouter] = MikrotikRouter.filter()
        tasks = (get_oid_data(router, counter) for router in routers)
        await asyncio.gather(*tasks)
        counter += 1
        await asyncio.sleep(5)


# endregion

# region SSH

async def get_logs():
    while True:
        routers: list[MikrotikRouter] = MikrotikRouter.filter()
        for router in routers:
            if router.is_online:
                asyncio.create_task(router.get_logs())
        await asyncio.sleep(20)


# endregion
