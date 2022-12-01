from time import perf_counter
import pandas as pd
import aiohttp
import asyncio
import json

# ** MAIN URL :
main_url = r"https://www.kohls.com/catalog/kids.jsp"


def load_headers(filename):
    with open(filename, "r") as file:
        headers = json.load(file)
        return headers


async def get_data(session, main_url, page_num, count=[]):
    params = {
        "CN": "AgeAppropriate:Kids",
        "pfm": "browse",
        "PPP": "48",
        "WS": f"{page_num * 48}",
        "S": "1",
        "sks": "true",
        "kls_sbp": "40129837192729573523974567636423216807",
        "ajax": "true",
        "gNav": "false"
    }
    async with session.get(main_url, params=params) as response:
        if response.status != 200:
            response.raise_for_status()
        count.append(1)
        print(f"Page: {len(count)} - Code: {response.status}")
        return await response.json()


async def fetch_all(fetch, session, main_url, data_list):
    tasks = []
    for value in data_list:
        task = asyncio.create_task(fetch(session, main_url, value))
        tasks.append(task)
    return await asyncio.gather(*tasks)


async def main_runner(fetch, main_url, data_list):
    async with aiohttp.ClientSession(headers=headers) as session:
        return await fetch_all(fetch, session, main_url, data_list)


def parse_json(page):
    products = page["products"] if page.get(
        "products") is not None else []
    if not products:
        return []
    list_products = []
    for product in products:
        dict_ = {
            "Product Title": product["productTitle"] if product.get("productTitle") is not None else "",
            "Product Image Url": product["image"]["url"] if product.get("image") is not None else "",
            "Product Average Rating": product["rating"]["avgRating"]if product.get("rating") is not None else "",
            "Product Sales Price": product["pricing"]["salePrice"]if product.get("pricing") is not None else "",
            "Product Regular Price": product["pricing"]["regularPrice"]if product.get("pricing") is not None else "",
        }
        list_products.append(dict_)
    return list_products


def write_data_to_excel(file_name, list_):
    df = pd.DataFrame(list_)
    df.to_excel(file_name, index=True, index_label="Entry Index")


if __name__ == "__main__":

    # ** Starting The Program :
    runtime_start = perf_counter()
    master_list = []

    # ** Loading Cookies from json file :
    headers = load_headers("headers.json")

    # ** Scraping The Pages to get The Products from the website :
    num_pages = 20  # the total number of pages is : 1302
    data_list = list(range(num_pages))

    # ** - 1 - Starting The Event Loop :
    t1 = perf_counter()
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(main_runner(
        get_data, main_url, data_list))

    # ** - 2 - Parsing The Inventory Data :
    for index, page in enumerate(results):
        try:
            master_list.extend(parse_json(page))
        except:
            print(f"An Error has occurred in page {index + 1}")

    del results

    t2 = perf_counter()
    print(
        f"Total: {len(master_list)} products in {t2 - t1: .2f} seconds")

    # ** Saving results to the excel sheet :
    write_data_to_excel("kohls__kids.xlsx", master_list)

    # ** End Program Run Time
    runtime_end = perf_counter()
    print(
        f"\nFile Saved...Total Runtime: {(runtime_end - runtime_start) / 60: .2f} Minutes.")
