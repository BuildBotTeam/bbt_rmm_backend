from pysnmp.hlapi.asyncio import *

OIDS = {
    '1.3.6.1.2.1.31.1.1.1.6.1': 'bytes-in',
    '1.3.6.1.2.1.31.1.1.1.10.1': 'bytes-out',
}


async def get_oid_data():
    error_indication, error_status, error_index, var_binds = await getCmd(
        SnmpEngine(),
        CommunityData('public', mpModel=1),
        UdpTransportTarget((IP_MIKROTIK, 161)),
        ContextData(),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.31.1.1.1.6.1')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.31.1.1.1.10.1')),
        lookupMib=False,
        lexicographicMode=False
    )

    if error_indication:
        print(error_indication)
    elif error_status:
        print('%s at %s' % (error_status.prettyPrint(), error_index and var_binds[int(error_index) - 1][0] or '?'))
    else:
        result_list = []
        for var_bind in var_binds:
            oid, data = [x.prettyPrint() for x in var_bind]
            result_list.append({'name': OIDS[oid], 'data': data})
        return result_list
