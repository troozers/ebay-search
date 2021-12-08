#!/usr/bin/env python3
import pandas as pd
from datetime import datetime
from ebaysdk.finding import Connection as Finding
from ebaysdk.exception import ConnectionError


class eBay(object):

    def __init__(self, search):
        self.api_key = "AndyStew-searchne-PRD-a7c924ccb-247abd5b"
        self.search = search
        self.timestamp = datetime.now().strftime('%A - %d-%b-%Y - %H:%M')
        pd.set_option('max_colwidth', 1000)
        pd.set_option('max_rows', 1000)

    def fetch(self):
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
            results = self.fetch()
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


def write_results(filename, data):
    # Output results to a markdown file
    with open(filename, 'w') as fn:
        print("# eBay Search Results", file=fn)
        print(f"## {ebay.timestamp}", file=fn)
        print("| Item | Image | Location | Price | Type | BiN? | End |", file=fn)
        print("| ---- | ----- | -------- | ----: | :--: | :--: | :-: |", file=fn)

        for key, val in data.iterrows():
            # Check Buy it Now Status
            if val['listingType'] == "Auction":
                buyitnow = "Yes" if val['buyItNowAvailable'] == "true" else "No"
            else:
                buyitnow = "Yes"

            # Output each row of results
            print(f"| [{val['title'][0:25]}...]({val['viewItemURL']} \"{val['title']}\")  "
                  f"| ![image]({val['galleryURL']}) "
                  f"| {val['location'].removesuffix(',United Kingdom')} "
                  f"| `{val['currentPrice']}` "
                  f"| {val['listingType']} "
                  f"| {buyitnow} "
                  f"| `{val['endTime'].strftime('%Y-%m-%d %H:%M')}` |",
                  file=fn)


if __name__ == '__main__':
    search = {'keywords': 'atari xl',
               'categoryId': ['162075'],
               'itemFilter': [{'name': 'LocatedIn', 'value': 'GB'},
                              {'name': 'MaxPrice', 'value': '100'}],
               'sortOrder': 'StartTimeNewest',
              }

    ebay = eBay(search)
    results = ebay.fetch()
    data = ebay.get_results(results)

    write_results('/home/andy/Downloads/eBay-Results.md', data)
