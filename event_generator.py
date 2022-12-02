'''
Generate events that go to the browser with Server Sent Events (SSE).
Materialize will push events whenever someone's bid has won an auction.
'''
import logging

import psycopg
from psycopg.sql import SQL, Identifier, Literal
from psycopg.rows import class_row
from fastapi import Request
from pydantic import BaseModel

from config import CLUSTER

_logger = logging.getLogger('uvicorn.error')

class WinningBid(BaseModel):
    # timestamp: int
    # diff: int
    auction_id: int
    bid_id: int
    item: str
    amount: int

async def event_generator(request: Request, conn: psycopg.AsyncConnection, amount: list[int] | None = None) -> WinningBid:
    '''
    Generate events that go to the browser with Server Sent Events (SSE).
    Materialize will push events whenever someone's bid has won an auction.
    '''
    try:
        while True:
            # Detect when user disconnects and exit the event loop
            if await request.is_disconnected():
                break
            # Asycronously get real-time updates from Materialize
            async with conn:
                async with conn.cursor(row_factory=class_row(WinningBid)) as cur:
                    # Set Materialize cluster
                    await cur.execute(SQL("SET CLUSTER = {}").format(Identifier('auction_house')))
                    _logger.info("Using Materialize cluster %s", CLUSTER)
                    # Subscribe to an endless stream of updates
                    if amount:
                        rows = cur.stream(
                            SQL("SUBSCRIBE (SELECT auction_id, bid_id, item, amount FROM winning_bids WHERE amount in ({}) )")
                                .format(SQL(', ').join(Literal(val) for val in amount))
                        )
                    else:
                        rows = cur.stream("SUBSCRIBE (SELECT auction_id, bid_id, item, amount FROM winning_bids)")
                    async for row in rows:
                        yield row
                
    except Exception as err:
        _logger.error(err)