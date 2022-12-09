import React, { useEffect, useState } from "react";
import Table from "../Table";

// ------------------------------
// | Code created using ChatGTP |
// ------------------------------
function parse(str: String): Auction {
    // Define the string to be parsed
    // const str = "auction_id=1574 bid_id=15742 item='City Bar Crawl' amount=55";

    // Create an empty object to store the parsed data
    const obj: any = {};

    // Use a regular expression to find all key-value pairs in the string
    const matches = str.match(/(?:[^\s']+|'[^']*')+/g);

    // Iterate over the resulting array of matches
    matches && matches.forEach(match => {
        // Split each match on the = character
        const [key, value] = match.split("=");

        // Set the property on the object using the key and value
        obj[key] = value;
    });

    // Print the resulting object
    return obj;
}

function parse_amount(str: string | null | undefined): string {

    if (!str) {
        return ""
    }
    var amounts = str.split(',');
    if (!amounts) {
        return ""
    }
    var result = "?"
    while (amounts.length > 0) {
        const current_amount = amounts.pop();
        result += `amount=${current_amount}&`;
    }
    result = result.replace(/&$/,'');
    return result;
}

export interface Auction {
    item: String;
    amount: String;
    auction_id: String;
    bid_id: String;
}

interface Props {
    value: string | null | undefined;
}

export default function Test(props: Props) {
    const [auctions, setAuctions] = useState<Array<Auction>>([]);
    const { value } = props;
    const amount = parse_amount(value)

    useEffect(() => {
        const url = `http://localhost:8000/subscribe${amount}`

        if ('EventSource' in window) {
          const source = new EventSource(url);
            if (source) {
                const dataListener: Array<Auction> = [];
                const listener = (e: any) => {

                    if (dataListener.length > 1000) {
                        dataListener.splice(0, 1);
                    }
                    dataListener.push(parse(e.data));

                    setAuctions([...dataListener]);
                };
                source.addEventListener('message', listener, false);

                return () => {
                    source.removeEventListener('message',listener);
                    setAuctions([]);
                }
            }
        }
    }, [value]);

    return (
        <div>
            <Table auctions={auctions}/>
        </div>
    )
}