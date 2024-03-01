# Real Time Auctions Powered by Materialize

## Introduction
The [Materialize quickstart](https://materialize.com/docs/get-started/) is a great way to get to know the database through an authentic example of an online auction house, where people auction items for sale, and others bid to buy those items.

The purpose of this repo is to use a language driver to connect to Materialize from an application just as you would connect to a PostgreSQL database. Here, we have a webserver built with `fastapi` that reads auction winners from Materialize in real-time using Server Sent Events. We build upon the [psycopg3 example in the docs](https://materialize.com/docs/integrations/python/#streaming-with-psycopg3) to make the database connection asynchronous and to add Server Sent Events with `sse_starlette`.

Another great thing about Materialize is that it supports Strict Serializability, which is the [highest level of consistency](http://jepsen.io/consistency). In our application, that means every observer at any given time will agree on the highest bid price for an item. Other stream processors can only offer eventual consistency, which would require us to, first, learn a complex stream processing framework, and second, implement extra logic in our application to account for edge cases introduced by eventual consistency. Instead, we just read from Materialize like we would any Postgres database, rest-assured by strong consistency, without having to care that it's powered by an [awesome stream processing engine underneath](https://timelydataflow.github.io/differential-dataflow/).

## Quick Video
[![short video demo](https://img.youtube.com/vi/smAkr--SIJc/0.jpg)](https://youtu.be/smAkr--SIJc_0)
## Setup

### Materialize Database
This web application assumes the existence of a Materialize database with the Auction House demo data available.

1. [Sign up for Materialize](https://www.materialize.com/register)
1. Enable a region
1. Create an App Password
1. Fill out your database connection details as environment variables in a file called `.env`. Here is an example:
    ```
    export MZ_HOST=<id>.<region>.aws.materialize.cloud
    export MZ_USER=chuck@materialize.com
    export MZ_PASSWORD=<app password>
    export MZ_PORT=6875
    export MZ_DB=materialize
    export MZ_CLUSTER=chuck
    export MZ_SCHEMA=public
    export MZ_TRANSACTION_ISOLATION="strict serializable"
    ```


1. Head to the [console SQL shell](https://console.materialize.com) and create resources and get real-time auction house data flowing. You can choose to isolate this example by creating a separate schema and cluster.

    ```sql
    CREATE SOURCE IF NOT EXISTS auction_house_source
    FROM LOAD GENERATOR AUCTION (TICK INTERVAL '100ms') 
    FOR ALL TABLES;

    CREATE VIEW on_time_bids AS
        SELECT
            bids.id       AS bid_id,
            auctions.id   AS auction_id,
            auctions.seller,
            bids.buyer,
            auctions.item,
            bids.bid_time,
            auctions.end_time,
            bids.amount
        FROM bids
        JOIN auctions ON bids.auction_id = auctions.id
        WHERE bids.bid_time < auctions.end_time;

    CREATE VIEW highest_bid_per_auction AS
        SELECT grp.auction_id, bid_id, buyer, seller, item, amount, bid_time, end_time FROM
            (SELECT DISTINCT auction_id FROM on_time_bids) grp,
            LATERAL (
                SELECT * FROM on_time_bids
                WHERE auction_id = grp.auction_id
                ORDER BY amount DESC LIMIT 1
            );

    CREATE VIEW winning_bids AS
        SELECT * FROM highest_bid_per_auction
        WHERE end_time < mz_now();

    CREATE INDEX winning_bids_idx_amount ON winning_bids (amount);
    ```

### Server

Create a virtual environment and install required dependencies.

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Run

1. Run the server
        
        uvicorn main:app

1. Open http://localhost:8000/subscribe in your browser or with `curl` to receive a continuous stream of winning bids (past, present, and future).

1. You can also include query parameters for `amount` to get real-time updates on auctions that were won with specific dollar amounts, like 
    - http://localhost:8000/subscribe/?amount=95
    - http://localhost:8000/subscribe/?amount=83&amount=84&amount=85&amount=97

    This is actually **very** cool. Other real-time stream processors would spin up new dataflows for each client, which is not scalable. Since we are reading off an in-memory index, Materialize serves the results to each client with efficient random access -- no extra dataflows are necessary.

## Run the frontend

1. Start

        yarn start
    
2. Go to http://localhost:3000 in your browser.


See [frontend](./frontend/README.md) for more setup details.

## Teardown

Back in the SQL shell:
```sql
DROP SOURCE auction_house_source CASCADE;
```
If you created a separate cluster and schema, make sure to drop them too! Here is an example if you named the cluster and schema both `auction_house`.
```sql
DROP SCHEMA auction_house CASCADE;
DROP CLUSTER auction_house CASCADE;
```

## Shout outs

Shout out to
- https://github.com/harshitsinghai77/server-sent-events-using-fastapi-and-reactjs
- https://github.com/bobbyiliev/materialize-tutorials/tree/main/mz-fastapi-demo
