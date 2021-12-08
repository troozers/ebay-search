#!/usr/bin/env python3
import pandas as pd
from datetime import datetime
from ebaysdk.finding import Connection as Finding
from ebaysdk.exception import ConnectionError

pd.set_option('max_colwidth', 1000)
pd.set_option('max_rows', 1000)
APPLICATION_ID = "AndyStew-searchne-PRD-a7c924ccb-247abd5b"
FILENAME = "/home/andy/Downloads/eBay-Results.md"
TIMESTAMP = datetime.now().strftime('%A - %d-%b-%Y - %H:%M')

search = {
    'keywords': 'atari xl',
    'categoryId': ['162075'],
    'itemFilter': [
        {'name': 'LocatedIn', 'value': 'GB'},
        {'name': 'MaxPrice', 'value': '100'}
    ],
    'sortOrder': 'StartTimeNewest',
}


def get_results(payload):
    try:
        api = Finding(siteid="EBAY-GB", appid=APPLICATION_ID, config_file=None)
        response = api.execute('findItemsAdvanced', payload)
        return response.dict()
    except ConnectionError as e:
        print(e)
        print(e.response.dict())


def get_total_pages(results):
    if results:
        return int(results.get('paginationOutput').get('totalPages'))
    else:
        return


def search_ebay(payload):
    """Search eBay with --search keywords with --category and return a list into a markdown document"""
    results = get_results(payload)
    total_pages = get_total_pages(results)
    items_list = results['searchResult']['item']

    i = 2
    while i <= total_pages:
        payload['paginationInput'] = {'entriesPerPage': 100, 'pageNumber': i}
        results = get_results(payload)
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


if __name__ == '__main__':
    ebay_results = search_ebay(search)

    # Output results to a markdown file
    with open(FILENAME, 'w') as fn:
        print("# eBay Search Results", file=fn)
        print(f"## {TIMESTAMP}", file=fn)
        print("| Item | Image | Location | Price | Type | BiN? | End |", file=fn)
        print("| ---- | ----- | -------- | ----: | :--: | :--: | :-: |", file=fn)

        for key, val in ebay_results.iterrows():
            # Check Buy it Now Status
            if val['listingType'] == "Auction":
                BiN = "Yes" if val['buyItNowAvailable'] == "true" else "No"
            else:
                BiN = "Yes"

            # Output each row of results
            print(f"| [{val['title'][0:25]}...]({val['viewItemURL']} \"{val['title']}\")  "
                  f"| ![image]({val['galleryURL']}) "              
                  f"| {val['location'].removesuffix(',United Kingdom')} "
                  f"| `{val['currentPrice']}` " 
                  f"| {val['listingType']} "
                  f"| {BiN} "
                  f"| `{val['endTime'].strftime('%Y-%m-%d %H:%M')}` |",
                  file=fn)
