import asyncio, asyncssh

from models.mikrotik import MikrotikRouter


async def run_client(router) -> asyncssh.SSHCompletedProcess:
    async with asyncssh.connect(router.host, username=router.username, password=router.password,
                                known_hosts=None) as conn:
        print('start logs')
        result = await conn.run('log print')
        router.add_logs(result.stdout.replace('\r', '').split('\n'))
        return result


async def get_logs():
    while True:
        routers: list[MikrotikRouter] = MikrotikRouter.filter()
        tasks = (run_client(router) for router in routers)
        await asyncio.gather(*tasks)
        await asyncio.sleep(20)
