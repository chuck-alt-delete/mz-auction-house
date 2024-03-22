'''
Generate events that go to the browser with Server Sent Events (SSE).
Materialize will push events whenever someone's bid has won an auction.
'''
import logging
from typing import List, Optional

import psycopg
from psycopg_pool import AsyncConnectionPool
from psycopg.sql import SQL, Placeholder
from psycopg.rows import class_row
from fastapi import Request
from pydantic import BaseModel

from config import DSN

_logger = logging.getLogger('uvicorn.error')
def log_db_diagnosis_callback(diagnosis: psycopg.Error.diag):
    '''Include database diagnostic messages in server logs'''
    _logger.info(f"The database says: {diagnosis.severity} - {diagnosis.message_primary}")

class WinningBid(BaseModel):
    '''Bid for an item at an auction'''
    mz_timestamp: int
    mz_progressed: Optional[bool] = None
    auction_id: Optional[int] = None
    bid_id: Optional[int] = None
    item: Optional[str] = None
    amount: Optional[int] = None

class SubscribeProgress(BaseModel):
    last_progress_mz_timestamp: int

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
        _logger.error(err)

async def notify_generator(
    request: Request,
    pool: AsyncConnectionPool,
    amount: list[int] | None = None) -> WinningBid:
    '''
    Generate events that will send a notification.
    Materialize will push events whenever someone's bid has won an auction.
    '''
    try:
        while True:
            if await request.is_disconnected():
                break
            as_of_ts: int = None
            async with pool.connection() as conn, conn.cursor(row_factory=class_row(SubscribeProgress)) as cur:
                conn.add_notice_handler(log_db_diagnosis_callback)
                # In this example we used a table in materialize to store the last_progress_mz_timestamp
                # But the user could store this in their own internal system.
                rows = await cur.execute("""
                                            SELECT last_progress_mz_timestamp
                                            FROM subscribe_progress
                                            WHERE subscribe_name = 'notify_winners'
                                            ORDER BY last_progress_mz_timestamp desc
                                            LIMIT 1
                     """)
                async for row in rows:
                    as_of_ts = row.last_progress_mz_timestamp
                    print("as of ts: ", as_of_ts)
            # Asycronously get real-time updates from Materialize
            async with pool.connection() as conn, conn.cursor(row_factory=class_row(WinningBid)) as cur:
                # Format query
                base_query = SQL("SELECT auction_id, bid_id, item, amount FROM winning_bids")
                if as_of_ts:
                   query = SQL("SUBSCRIBE ({}) WITH (PROGRESS, SNAPSHOT false) AS OF {}").format(base_query, as_of_ts)
                else:
                    query = SQL("SUBSCRIBE ({}) WITH (PROGRESS, SNAPSHOT true)").format(base_query)
                # Subscribe to an endless stream of updates
                # Todo: handle error where AS OF timestamp is past the retain history interval
                rows = cur.stream(query, amount)
                print("got rows, query: ", query)
                staged_data: List[WinningBid] = []
                async for row in rows:
                    print("row: ", row)
                    if row.mz_progressed:
                        print("in mz_progressed")
                        for staged_row in staged_data:
                            yield staged_row
                        staged_data.clear()
                        last_progress_mz_timestamp = row.mz_timestamp
                        
                        # TODO: make recording `last_progress_mz_timestamp` an async task that
                        # happens periodically.
                        # Ideally we'd be able to do `INSERT ... ON CONFLICT UPDATE ...`, or
                        # the server stores `last_progress_mz_timestamp` somewhere in their own
                        #  durable infrastructure (not within mz).  
                        print("writing last_progress_mz_timestamp ")
                        insert_conn = await psycopg.AsyncConnection.connect(DSN, autocommit=True)
                        async with insert_conn:
                            insert_conn.add_notice_handler(log_db_diagnosis_callback)
                            async with insert_conn.cursor() as insert_cursor:
                                if as_of_ts:
                                    await insert_cursor.execute(
                                        SQL("UPDATE subscribe_progress SET last_progress_mz_timestamp = {} WHERE subscribe_name = 'notify_winners'").format(last_progress_mz_timestamp)
                                        )
                                else:    
                                    await insert_cursor.execute(
                                            "INSERT INTO subscribe_progress (subscribe_name, last_progress_mz_timestamp) VALUES (%s, %s)",
                                                ('notify_winners',last_progress_mz_timestamp)                                        )
                        print("wrote last_progress_mz_timestamp ")
                    else:
                        staged_data.append(row)                    
                # Detect when user disconnects and exit the event loop
                if await request.is_disconnected():
                    await conn.close()
                    break

    except Exception as err:
        _logger.error(err)
