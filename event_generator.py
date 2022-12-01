'''
Generate events that go to the browser with Server Sent Events (SSE).
Materialize will push events whenever someone's bid has won an auction.
'''
import logging

import psycopg
from psycopg.sql import SQL, Identifier
from fastapi import Request

from config import CLUSTER

_logger = logging.getLogger('uvicorn.error')

async def event_generator(request: Request, conn: psycopg.AsyncConnection):
    '''
    Generate events that go to the browser with Server Sent Events (SSE).
    Materialize will push events whenever someone's bid has won an auction.
    '''
    try:
        while True:
            # Detect when user disconnects and exit the event loop
            if await request.is_disconnected():
                break

            yield "wait a moment..."

            # Asycronously get real-time updates from Materialize
            async with conn:
                async with conn.cursor() as cur:
                    
                    # Set Materialize cluster
                    await cur.execute(SQL("SET CLUSTER = {}").format(Identifier('auction_house')))
                    _logger.info("Using Materialize cluster %s", CLUSTER)

                    # Subscribe to an endless stream of updates
                    async for row in cur.stream(
                    """SUBSCRIBE (
                            SELECT auction_id, bid_id, item, amount
                            FROM winning_bids
                        )
                    """):
                        yield row
                
    except Exception as err:
        _logger.error(err)