import React from "react";
import { Auction } from "../subscribe";

interface Props {
    auctions: Array<Auction>;
}

function Table(props: Props) {
    const { auctions } = props;

    return (
      <div className="px-4 sm:px-6 lg:px-8 mt-10">
        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto">
            <h1 className="text-2xl font-semibold text-gray-900">Live auctions</h1>
            <p className="mt-2 text-sm text-gray-700">
              From the auctions house
            </p>
          </div>
        </div>
        <div className="mt-8 flex flex-col">
          <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
            <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
              <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                <table className="min-w-full divide-y divide-gray-300">
                  <thead className="bg-gray-50">
                    <tr>
                      <th
                        scope="col"
                        className="whitespace-nowrap px-2 py-3.5 text-left text-sm font-semibold text-gray-900"
                      >
                        Item
                      </th>
                      <th
                        scope="col"
                        className="whitespace-nowrap px-2 py-3.5 text-left text-sm font-semibold text-gray-900"
                      >
                        Amount
                      </th>
                      <th
                        scope="col"
                        className="whitespace-nowrap px-2 py-3.5 text-left text-sm font-semibold text-gray-900"
                      >
                        Auction ID
                      </th>
                      <th
                        scope="col"
                        className="whitespace-nowrap px-2 py-3.5 text-left text-sm font-semibold text-gray-900"
                      >
                        Bid ID
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white">
                    {auctions.map(({ item, amount, auction_id, bid_id }) => (
                      <tr key={bid_id.toString()}>
                        <td className="whitespace-nowrap px-2 py-2 text-sm font-medium text-gray-900">
                          {item}
                        </td>
                        <td className="whitespace-nowrap px-2 py-2 text-sm text-gray-500">{amount}</td>
                        <td className="whitespace-nowrap px-2 py-2 text-sm text-gray-500">{auction_id}</td>
                        <td className="whitespace-nowrap px-2 py-2 text-sm text-gray-500">{bid_id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  Table.defaultProps = {
    auctions: [],
  }

  export default Table;