import hmac
from datetime import datetime, timedelta
import hashlib
import time
import requests
import json
import pyshopee
# import sys


def shopee_shop_auth():
    # intentionally to be run with or without Frappe
    timest = int(time.time())
    # timest = int(datetime.timestamp(datetime.now())) # get timestamp
    # timest = int(datetime.timestamp(datetime.utcnow() + timedelta(hours=8))) # get timestamp

    host = "https://partner.test-stable.shopeemobile.com"
    # host = "https://partner.shopeemobile.com"
    path = "/api/v2/shop/auth_partner"
    # redirect_url = "https://www.google.com"
    redirect_url = "https://naturetonurture.rayasolutions.store/api/method/nton_app.api.shopee_test_func"
    partner_id = 1067444
    tmp = "515864624e49634164484c4470734b4c755375456f435a7479505a74624e6b6f"
    partner_key = tmp.encode()
    tmp_base_string = "%s%s%s" % (partner_id, path, timest)
    base_string = tmp_base_string.encode()
    sign = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()
    ##generate api
    url = host + path + "?partner_id=%s&timestamp=%s&sign=%s&redirect=%s" % (partner_id, timest, sign, redirect_url)
    print(url)
    print("Sign:",sign)

print("Date:",(datetime.utcnow() + timedelta(hours=8)))
shopee_shop_auth()

def time_diff(d,h,m,s): # days, hours, minutes, seconds (include negative sign if necessary)
    timeNow = int(datetime.timestamp(datetime.utcnow() + timedelta(hours=8))) # get timestamp
    timeNowDiff = int(datetime.timestamp(datetime.utcnow() + timedelta(hours=8) + timedelta(days=d,hours=h,minutes=m,seconds=s)))
    print("Timestamp now:",timeNow)
    print("Timestamp with difference (d=%d,h=%d,m=%d,s=%d): %d" % (d,h,m,s,timeNowDiff))
    print("Timestamp with time library:", int(time.time())) # produces same output as utcnow() + 8hrs!

time_diff(-14,0,0,0)

def shopee_sdk_test():
    shopid = 93614
    partnerid = 1067444
    api_key = "515864624e49634164484c4470734b4c755375456f435a7479505a74624e6b6f"
    client = pyshopee.Client( shopid, partnerid, api_key )

    # get_order_by_status (UNPAID/READY_TO_SHIP/SHIPPED/COMPLETED/CANCELLED/ALL)
    resp = client.order.get_order_by_status(order_status="READY_TO_SHIP")
    print(resp)

shopee_sdk_test()

def lazada_test():
    # headers = {"Content-Type": "application/json"}
    resp = requests.get("https://api.lazada.com.ph/rest/orders/get?sort_direction=DESC&offset=0&created_after=1999-10-10T16%3A00%3A00%2B08%3A00&limit=30&sort_by=updated_at&status=ready_to_ship&app_key=126275&sign_method=sha256&access_token=50000600621qhqtLfuBiCwVuR9b2otcpQ18526e15h0rCYEjrgkTuefILEHM1Ppg&timestamp=1695839744760&sign=7AD8CEC1F07333937DB359F536DD745F49657B658AFFFC0F9487E5F28B34A9B8")
    ret = json.loads(resp.content)
    all_orders = ret["data"]["orders"]
    print("Number of orders ready:",ret["data"]["countTotal"])
    # print(ret)
    list_of_orders = []
    for order in all_orders:
        new_doctype = {}
        new_doctype["order_number"] = order["order_number"]
        new_doctype["customer_first_name"] = order["customer_first_name"]
        new_doctype["payment_method"] = order["payment_method"]
        new_doctype["price"] = order["price"]
        new_doctype["order_status"] = order["statuses"][0]
        # print("New order")
        # print(new_doctype)
        list_of_orders.append(new_doctype)
    
    add_item = frappe.get_doc({
        "doctype": "Lazada Order List Update",
        "count": ret["data"]["countTotal"],
        "order": list_of_orders
    })

    add_item.insert()
    frappe.db.commit()

    return add_item


# lazada_test()