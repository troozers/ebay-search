#!/usr/bin/env python3
import click
import json
import pandas as pd
from datetime import datetime
from ebaysdk.finding import Connection as Finding
from ebaysdk.exception import ConnectionError


class eBayConnect(object):

    def __init__(self, api_key):
        self.api_key = api_key
        self.search = dict()
        self.timestamp = datetime.now().strftime('%A - %d-%b-%Y - %H:%M')
        pd.set_option('max_colwidth', 1000)
        pd.set_option('max_rows', 1000)

    def look_for(self, search):
        self.search = search
        try:
            api = Finding(siteid="EBAY-GB", appid=self.api_key, config_file=None)
            response = api.execute('findItemsAdvanced', self.search)
            return response.dict()
        except ConnectionError as e:
            print(e)
            print(e.response.dict())

    @staticmethod
    def total_pages(results):
        if results:
            return int(results.get('paginationOutput').get('totalPages'))
        else:
            return

    def get_results(self, results):
        total_pages = self.total_pages(results)
        items_list = results['searchResult']['item']

        i = 2
        while i <= total_pages:
            self.search['paginationInput'] = {'entriesPerPage': 100, 'pageNumber': i}
            results = self.look_for(self.search)
            items_list.extend(results['searchResult']['item'])
            i += 1

        df_items = pd.DataFrame(columns=['title', 'viewItemURL', 'galleryURL', 'location', 'postalCode',
                                         'listingType', 'buyItNowAvailable', 'currentPrice', 'endTime'])

        for item in items_list:
            row = {
                'title': item.get('title'),
                'viewItemURL': item.get('viewItemURL'),
                'galleryURL': item.get('galleryURL'),
                'location': item.get('location'),
                'postalCode': item.get('postalCode'),
                'listingType': item.get('listingInfo').get('listingType'),
                'buyItNowAvailable': item.get('listingInfo').get('buyItNowAvailable'),
                'currentPrice': f"{float(item.get('sellingStatus').get('currentPrice').get('value')):.2f}",
                'endTime': datetime.fromisoformat(item.get('listingInfo').get('endTime').replace("Z", "+00:00")),
            }

            df_items = df_items.append(row, ignore_index=True)

        return df_items


def write_results(filename, items):
    # Output results to a markdown file
    with open(filename, 'w') as fn:
        print("# eBay Search Results", file=fn)
        print(f"## {ebay.timestamp}", file=fn)
        print(f"Searching for:", file=fn)
        print(f"```json\n{json.dumps(ebay.search, indent=4)}\n```", file=fn)
        print("| Item | Image | Location | Price | Type | BiN? | End |", file=fn)
        print("| ---- | ----- | -------- | ----: | :--: | :--: | :-: |", file=fn)

        for key, item in items.iterrows():
            # Check Buy it Now Status
            if item['listingType'] == "Auction":
                buyitnow = "Yes" if item['buyItNowAvailable'] == "true" else "No"
            else:
                buyitnow = "Yes"

            # Output each row of results
            print(f"| [{item['title'][0:25]}...]({item['viewItemURL']} \"{item['title']}\")  "
                  f"| ![image]({item['galleryURL']}) "
                  f"| {item['location'].removesuffix(',United Kingdom')} "
                  f"| `{item['currentPrice']}` "
                  f"| {item['listingType']} "
                  f"| {buyitnow} "
                  f"| `{item['endTime'].strftime('%Y-%m-%d %H:%M')}` |",
                  file=fn)


@click.command()
@click.option('--keywords', '-k', required=True, help='Keywords to search eBay for.')
@click.option('--maxprice', '-m', default='999.99', help='Maximum price willing to pay for the item. (default=999.99)')
@click.option('--category', '-c', required=True, help='Which category id to look in.')
@click.option('--filename', '-o', required=True, help='Name of markdown file to create.')
def get_results(keywords, maxprice, category, filename):
    """Utility to search eBay for --keywords and return the items in a markdown file."""

    my_stuff = dict(keywords=keywords, categoryId=[category], itemFilter=[{'name': 'LocatedIn', 'value': 'GB'},
                                                                          {'name': 'MaxPrice', 'value': maxprice}],
                    sortOrder='startTimeNewest')

    found = ebay.look_for(my_stuff)
    data = ebay.get_results(found)
    write_results(filename, data)


if __name__ == '__main__':
    ebay = eBayConnect(api_key='AndyStew-searchne-PRD-a7c924ccb-247abd5b')
    get_results()
