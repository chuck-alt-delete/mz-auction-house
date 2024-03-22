'''
Generate events that go to the browser with Server Sent Events (SSE).
Materialize will push events whenever someone's bid has won an auction.
'''
import logging

import psycopg
from psycopg_pool import AsyncConnectionPool
from psycopg.sql import SQL, Placeholder
from psycopg.rows import class_row
from fastapi import Request
from pydantic import BaseModel

_logger = logging.getLogger('uvicorn.error')
def log_db_diagnosis_callback(diagnosis: psycopg.Error.diag):
    '''Include database diagnostic messages in server logs'''
    _logger.info(f"The database says: {diagnosis.severity} - {diagnosis.message_primary}")

class WinningBid(BaseModel):
    '''Bid for an item at an auction'''
    auction_id: int
    bid_id: int
    item: str
    amount: int

async def event_generator(
    request: Request,
    pool: AsyncConnectionPool,
    amount: list[int] | None = None) -> WinningBid:
    '''
    Generate events that go to the browser with Server Sent Events (SSE).
    Materialize will push events whenever someone's bid has won an auction.
    '''
    try:
        while True:
            if await request.is_disconnected():
                break
            # Asycronously get real-time updates from Materialize
            async with pool.connection() as conn, conn.cursor(row_factory=class_row(WinningBid)) as cur:
                conn.add_notice_handler(log_db_diagnosis_callback)
                # Format query
                base_query = SQL("SELECT auction_id, bid_id, item, amount FROM winning_bids")
                if amount:
                    # Construct the 'IN' clause with placeholders for each amount value
                    placeholders = SQL(', ').join(Placeholder() * len(amount))
                    where_clause = SQL(" WHERE amount IN ({})").format(placeholders)
                    
                    # Combine the base query with the WHERE clause
                    query = SQL("SUBSCRIBE ({})").format(base_query + where_clause)
                else:
                    # If 'amount' is empty, use the base query without WHERE clause
                    query = SQL("SUBSCRIBE ({})").format(base_query)
                # Subscribe to an endless stream of updates
                rows = cur.stream(query, amount)
                async for row in rows:
                    yield row
                # Detect when user disconnects and exit the event loop
                if await request.is_disconnected():
                    await conn.close()
                    break
    except Exception as err:
        _logger.exception(err)
