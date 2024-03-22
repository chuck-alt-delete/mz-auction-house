'''
Generate events that go to the browser with Server Sent Events (SSE).
Materialize will push events whenever someone's bid has won an auction.
'''

import logging
from psycopg_pool import AsyncConnectionPool
from psycopg import conninfo
from sse_starlette.sse import EventSourceResponse
from fastapi import FastAPI, Request, Query
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import config
from event_generator import event_generator, notify_generator, WinningBid

# Logging stuff
_logger = logging.getLogger('uvicorn.error')
# Connect _logger with FastAPI's logging
logger.handlers = _logger.handlers


# Init FastAPI app
app = FastAPI()


origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def open_pool():
    """create database connection pool"""
    app.state.pool = AsyncConnectionPool(
        conninfo = conninfo.make_conninfo(
            user = config["MZ_USER"],
            dbname = config["MZ_DB"],
            host = config["MZ_HOST"],
            password = config["MZ_PASSWORD"],
            port = 6875,
            application_name = 'FastAPI',
            options = config["options"],
        ),
        max_size = 500,
        min_size = 5
    )

@app.on_event("shutdown")
async def close_pool():
    """close database connection pool"""
    await app.state.pool.close()


@app.get("/")
async def root():
    '''Shill Materialize'''
    return {"message": "Hello world. Check out materialize.com!"}

@app.get("/subscribe/", response_model=WinningBid)
async def message_stream(request: Request, amount: list[int] | None = Query(default=None)):
    '''Retrieve events from the event generator for SSE'''
    return (EventSourceResponse(notify_generator(request, app.state.pool, amount)))

if __name__ == "__main__":
    logger.setLevel(_logger.level)
    uvicorn.run(app, host="127.0.0.1", port=8000)
