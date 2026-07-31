import base64

import requests
import json
import os
import xmltodict
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID=os.getenv("CLIENT_ID")
RUNAME=os.getenv("RUNAME")
CLIENT_SECRET=os.getenv("CLIENT_SECRET")
REFRESH_TOKEN=os.getenv("REFRESH_TOKEN")
EBAY_SCOPE = os.getenv("SCOPE")
CATEGORY_ID = "11116"

def get_access_token():
    url = "https://api.ebay.com/identity/v1/oauth2/token"

    auth_header = base64.b64encode(
        f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    ).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_header}"
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "scope": EBAY_SCOPE
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def get_inventory_items(access_token):
    all_items = []
    page = 1

    URL = "https://api.ebay.com/ws/api.dll"

    while True:
        xml_body = f"""
                <?xml version="1.0" encoding="utf-8"?>
                <GetMyeBaySellingRequest xmlns="urn:ebay:apis:eBLBaseComponents">
                  <RequesterCredentials>
                    <eBayAuthToken>{access_token}</eBayAuthToken>
                  </RequesterCredentials>
                  <ActiveList>
                    <Include>true</Include>
                    <Pagination>
                      <EntriesPerPage>200</EntriesPerPage>
                      <PageNumber>{page}</PageNumber>
                    </Pagination>
                  </ActiveList>
                </GetMyeBaySellingRequest>
                """
        headers = {
            "X-EBAY-API-CALL-NAME": "GetMyeBaySelling",
            "X-EBAY-API-SITEID": "0",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "1149",
            "Content-Type": "text/xml"
        }

        response = requests.post(URL, data=xml_body, headers=headers)
        data = xmltodict.parse(response.text)
        resp = data["GetMyeBaySellingResponse"]
        # Stop if no more pages
        active = resp.get("ActiveList", {})
        items = active.get("ItemArray", {}).get("Item")

        if not items:
            break
        if isinstance(items, dict):
            items = [items]

        all_items.extend(items)
        page += 1

    return all_items

def get_item_data(access_token, item_id):
    URL = "https://api.ebay.com/ws/api.dll"
    xml_body = f"""
            <?xml version="1.0" encoding="utf-8"?>
            <GetItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
                <RequesterCredentials>
                    <eBayAuthToken>{access_token}</eBayAuthToken>
                </RequesterCredentials>
                <ItemID>{item_id}</ItemID>
                <DetailLevel>ReturnAll</DetailLevel>
            </GetItemRequest>
            """
    headers = {
        "X-EBAY-API-CALL-NAME": "GetItem",
        "X-EBAY-API-SITEID": "0",
        "X-EBAY-API-COMPATIBILITY-LEVEL": "1149",
        "Content-Type": "text/xml"
    }
    response = requests.post(URL, data=xml_body, headers=headers)
    data = xmltodict.parse(response.text)
    item = data["GetItemResponse"]["Item"]
    category = item["PrimaryCategory"]["CategoryName"]
    pics = item['PictureDetails']['PictureURL']
    if isinstance(pics, str):
        return category, pics
    return category, pics[0]

def get_listing_data():
    access_token = get_access_token()
    items = get_inventory_items(access_token)

    results = []


    for item in items:
        item_id = item.get("ItemID")
        category, picture_link = get_item_data(access_token, item_id)
        if "Coins & Paper Money" in category:
            title = item.get("Title")
            price_float = float(item.get("BuyItNowPrice", {}).get("#text"))
            price = "C $" + f"{price_float:.2f}"
            link = item.get("ListingDetails", {}).get("ViewItemURL")
            tags = get_tags(title, category)
            desc = get_desc(tags)
            product = {
                "name": title,
                "tags": tags,
                "desc": desc,
                "photo": picture_link,
                "price": price,
                "link": link
            }
            results.append(product)

    return results

def get_desc(tags: str):
    desc = "eBay"
    if "canadian" in tags:
        desc += " - Canadian Coins"
    else:
        desc += " - American Coins"
    if "ungraded" in tags:
        desc += " - Ungraded"
    else:
        desc += " - Graded"
    for denom in ["NGC", "PCGS", "ICCS", "ICG"]:
        if denom.lower() in tags:
            desc += " - " + denom
    return desc

def get_tags(title: str, category: str):
    tags = "all product ebay"
    if "canada" in category.lower():
        tags += " canadian"
    else:
        tags += " american"
    # Grading companies
    if "ngc" in title.lower():
        tags += " graded ngc"
    elif "pcgs" in title.lower():
        tags += " graded pcgs"
    elif "icg" in title.lower():
        tags += " graded icg"
    elif "iccs" in title.lower():
        tags += " graded iccs"
    else:
        tags += " ungraded"

    # Denominations
    denoms = ["Large Cents", "Small Cents", "Five Cents", "Ten Cents", "Twenty Cents", "Twenty-Five Cents", "Fifty Cents", "One Dollar", "Two Dollars", "Commemorative"]
    for i in range(0, 9):
        if denoms[i] in category.lower():
            if i == 0 or i == 1:
                tags += " 1c"
            if i == 2 and denoms[5] not in category.lower():
                tags += " 5c"
            if i == 3:
                tags += " 10c"
            if i == 4:
                tags+= " 20c"
            if i == 5:
                tags += " 25c"
            if i == 6:
                tags += " 50c"
            if i == 7:
                tags += " $1"
            if i == 8:
                tags += " $2"
            if i == 9:
                tags += " commem"

    return tags

def write_to_json(listing_data):
    with open("products.json", "w") as file:
        json.dump(listing_data, file, indent=4)


if __name__ == "__main__":
    listing_data = get_listing_data()
    print(len(listing_data))
    write_to_json(listing_data)
