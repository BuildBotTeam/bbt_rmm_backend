import asyncio
from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware

from controllers.router_controller import get_logs
from views.mikrotik_router_app import mikrotik_router_app
from views.auth_app import auth_app, TokenAuthBackend
from views.bot_app import dp, bot

middleware = Middleware(CORSMiddleware,
                        allow_origins=["http://localhost:3000", "https://localhost:3000"],
                        allow_methods=["*"],
                        allow_headers=["*"],
                        )

app = FastAPI(middleware=[middleware])
app.mount('/auth', auth_app)
secure_app = FastAPI(middleware=[Middleware(AuthenticationMiddleware, backend=TokenAuthBackend())])
app.mount('/api', secure_app)
secure_app.mount('/mikrotik_routers', mikrotik_router_app)


@app.on_event('startup')
async def start_services():
    loop = asyncio.get_event_loop()
    loop.create_task(get_logs())
    loop.create_task(dp.start_polling(bot))


@app.on_event("shutdown")
async def shutdown_bot():
    await dp.stop_polling()
