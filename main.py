'''
Generate events that go to the browser with Server Sent Events (SSE).
Materialize will push events whenever someone's bid has won an auction.
'''

import logging
import psycopg
from sse_starlette.sse import EventSourceResponse
from fastapi import FastAPI, Request
from fastapi.logger import logger
import uvicorn


from event_generator import event_generator, WinningBid
from config import DSN

# Logging stuff
_logger = logging.getLogger('uvicorn.error')
# Connect _logger with FastAPI's logging
logger.handlers = _logger.handlers
def log_db_diagnosis_callback(diagnosis: psycopg.Error.diag):
    '''Include database diagnostic messages in server logs'''
    _logger.info(f"The database says: {diagnosis.severity} - {diagnosis.message_primary}")

app = FastAPI()

@app.get("/")
async def root():
    '''Shill Materialize'''
    return {"message": "Hello world. Check out materialize.com!"}

@app.get("/subscribe/", response_model=WinningBid)
async def message_stream(request: Request, amount: int | None = None):
    '''Create async database connection and retrieve events from the event generator for SSE'''
    conn = await psycopg.AsyncConnection.connect(DSN)
    conn.add_notice_handler(log_db_diagnosis_callback)
    return (EventSourceResponse(event_generator(request, conn, amount)))

if __name__ == "__main__":
    logger.setLevel(_logger.level)
    uvicorn.run(app, host="127.0.0.1", port=8000)
