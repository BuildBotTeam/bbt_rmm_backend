import asyncio
from datetime import datetime

from models.mikrotik import MikrotikRouter, MikrotikSNMPLogs
from pysnmp.hlapi.asyncio import *

from views.ws_app import manager
from pysnmp.hlapi import UsmUserData


# region SNMP

async def get_oid_data(router: MikrotikRouter, counter):
    error_indication, error_status, error_index, var_binds = await getCmd(
        SnmpEngine(),
        UsmUserData('SNMPv3', authKey=router.password, privKey=router.password,
                    authProtocol=usmHMACSHAAuthProtocol,
                    privProtocol=usmAesCfb128Protocol),
        UdpTransportTarget((router.host, 161), timeout=2.0),
        ContextData(),
        *[ObjectType(ObjectIdentity(oid)) for oid in router.oids.keys()],
        lookupMib=False,
        lexicographicMode=False
    )
    print(error_indication, error_status, error_index, var_binds)
    result = {'time': datetime.now().astimezone().isoformat()}
    if error_indication:
        if router.is_online:
            router.is_online = False
            result['online'] = False
            router.status_log.append(MikrotikSNMPLogs(**result))
            router.save()
            await manager.broadcast(router.user_id, 'update_router', router.model_dump(exclude={'password'}))
        return None

    if not router.is_online:
        router.is_online = True
        router.save()
        await manager.broadcast(router.user_id, 'update_router', router.model_dump(exclude={'password'}))

    if counter == 0:
        result_var_bind = []
        for var_bind in var_binds:
            oid, data = [x.prettyPrint() for x in var_bind]
            if '1.3.6.1.2.1.47.1.1.1.1.2.65536' == oid:  # version os
                if data != router.version_os:
                    router.version_os = data
                    await manager.broadcast(router.user_id, 'update_router', router.model_dump(exclude={'password'}))
                continue
            result_var_bind.append(f'{router.oids[oid]} - {data}')
        result['message'] = '; '.join(result_var_bind)
        router.status_log.append(MikrotikSNMPLogs(**result))
        router.save()


async def get_status():
    counter = 0
    while True:
        if counter == 20:
            counter = 0
        routers: list[MikrotikRouter] = MikrotikRouter.filter()
        for router in routers:
            asyncio.create_task(get_oid_data(router, counter))
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
        await asyncio.sleep(600)

# endregion
