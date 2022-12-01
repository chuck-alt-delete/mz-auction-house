# Real Time Auctions Powered by Materialize

## Introduction
The [Materialize quickstart](https://materialize.com/docs/get-started/) is a great way to get to know the database through an authentic example of an online auction house, where people auction items for sale, and others bid to buy those items.

The purpose of this repo is to add a client component beyond `psql`. Here, we have a webserver built with `fastapi` that reads auction winners from Materialize in real-time using Server Sent Events. One of the great features of Materialize is that it's Postgres wire compatible, so we can use the typical `psycopg` library just like any Postgres database. We build upon the [psycopg3 example in the docs](https://materialize.com/docs/integrations/python/#streaming-with-psycopg3) to make the database connection asynchronous and to add Server Sent Events with `sse_starlette`.

Another great thing about Materialize is that it supports Strict Serializability, which is the [highest level of consistency](http://jepsen.io/consistency). What that means in this demo is when our server receives an auction winner, we can be certain that person actually won the auction. We don't have to implement extra logic to account for eventual consistency (avoiding having to learn a complex stream processing framework in the process). We just read from Materialize like we would any Postgres database, and we don't have to care that it's powered by an [awesome stream processing engine underneath](https://timelydataflow.github.io/differential-dataflow/)

## Setup

### Materialize Database
This web application assumes the existence of a Materialize database with the Auction House demo data available.

1. [Sign up for Materialize](https://www.materialize.com/register)
1. Enable a region
1. Create an App Password
1. Fill out your database credentials in a file called `.env` and source those variables. See [example.env](./example.env) as reference.

        source .env

1. you can use this `psql` command to create resources and get real-time auction house data flowing:

    ```bash
    psql "postgres://$MZ_EMAIL_PREFIX%40$MZ_EMAIL_SUFFIX:$MZ_PASSWORD@$MZ_HOST:$MZ_PORT/$MZ_DB" << EOF
    CREATE SOURCE IF NOT EXISTS auction_house_source
    FROM LOAD GENERATOR AUCTION (TICK INTERVAL '1s') 
    FOR ALL TABLES 
    WITH (SIZE = '3xsmall');

    CREATE CLUSTER auction_house REPLICAS (xsmall_replica (SIZE 'xsmall'));
    SET CLUSTER = auction_house;

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

    CREATE DEFAULT INDEX winning_bids_idx ON winning_bids;

    EOF
    ```

### Server

Create a virtual environment and install required dependencies.

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Run

1. Run the server
        
        uvicorn main:app

1. Open http://localhost:8000/subscribe


## Teardown

```bash
psql "postgres://$MZ_EMAIL_PREFIX%40$MZ_EMAIL_SUFFIX:$MZ_PASSWORD@$MZ_HOST:$MZ_PORT/$MZ_DB" << EOF
DROP SOURCE auction_house_source CASCADE;
DROP CLUSTER auction_house CASCADE;
EOF
```

## Shout outs

Shout out to
- https://github.com/harshitsinghai77/server-sent-events-using-fastapi-and-reactjs
- https://github.com/bobbyiliev/materialize-tutorials/tree/main/mz-fastapi-demo