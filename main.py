import logging

import asyncio
import psycopg
from config import DSN
from sse_starlette.sse import EventSourceResponse
from fastapi import FastAPI, Request
from fastapi.logger import logger
import uvicorn

_logger = logging.getLogger('uvicorn.error')
logger.handlers = _logger.handlers

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/subscribe")
async def message_stream(request: Request):
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                yield "wait a moment..."
                with psycopg.connect(DSN) as conn:
                    with conn.cursor() as cur:
                        cur.execute("SET CLUSTER = auction_house")
                        _logger.info("made it here!")
                        cur.execute(
                        """DECLARE c CURSOR FOR SUBSCRIBE (
                                SELECT auction_id, bid_id, item, amount 
                                FROM winning_bids
                            )""")
                        cur.execute("FETCH ALL c WITH (timeout='1s')")
                        _logger.info("hello")
                        if not cur.fetchone():
                            _logger.info("no data yet")
                            yield "no data yet"
                            continue
                        else:
                            for row in cur:
                                yield row                   
        except Exception as err:
            _logger.error(err)

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    logger.setLevel(_logger.level)
    uvicorn.run(app, host="127.0.0.1", port=8000)
