import asyncio
from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from views.api_app import secure_app
from views.auth_app import auth_app
from views.bot_app import dp, bot

middleware = Middleware(CORSMiddleware,
                        allow_origins=["*"],
                        allow_methods=["*"],
                        allow_headers=["*"],
                        )

app = FastAPI(middleware=[middleware])
app.mount('/auth', auth_app)
app.mount('/api', secure_app)


@app.on_event('startup')
async def start_bot():
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling(bot, polling_timeout=300))


@app.on_event("shutdown")
async def shutdown_bot():
    await dp.stop_polling()

# api = connect('admin', 'admin')
# list = api.get_resource('/system/script')
# for l in list.get():
#     s = Script(**l)
#     print(s)
