import frappe
import pyshopee
import hmac
import json
import time
import requests
import hashlib
from urllib.request import urlopen
from datetime import datetime, date, timedelta
from erpnext.stock.utils import get_stock_balance
from random import randint

HOST_SB = "https://partner.test-stable.shopeemobile.com"
HOST = "https://partner.shopeemobile.com"
ORDER_PUSH = 3

def get_common_params(sandbox=False):
    auth = frappe.get_doc("Shopee Auth")
    access_token = auth.access_token if sandbox else auth.prod_access
    print("-----here---")
    print(auth.access_token)
    print(access_token)
    timestamp = int(time.time())
    print(timestamp)
    partner_id = 1067444 if sandbox else 2006532
    shop_id = 93614 if sandbox else 38167274
    sb_partner = (
        "515864624e49634164484c4470734b4c755375456f435a7479505a74624e6b6f"
    ).encode()
    pd_partner = (
        "70637a436d4947456552704d58575955525a4e6b73576e78746d4f74736b7551"
    ).encode()
    partner_key = sb_partner if sandbox else pd_partner
    print("access_token here")
    print(access_token)
    print(shop_id)
    print(partner_id)
    print(partner_key)

    #return ('544b737546656e65654948646b42434b', timestamp, '1067444', '93614',sb_partner)
    return (access_token, timestamp, partner_id, shop_id, partner_key)

def save_scratch_data(data, tags):
    doc = frappe.get_doc(
        {"doctype": "Shopee Logs", "content": str(data), "tags": str(tags)}
    )
    doc.insert()
    frappe.db.commit()

def get_sign(partner_key, base_string):
    return hmac.new(partner_key, base_string.encode(), hashlib.sha256).hexdigest()


@frappe.whitelist(allow_guest=True)
def shopee_sb_webhook():
    # req = json.loads(frappe.request.data)
    req = {"code":3,"verify_info": "Example verify only."}
    # try:
    #     order_status = kwargs2["data"]["order_status"]
    # except:
    #     order_status = "unknown"

    add_item = frappe.get_doc(
        {
            "doctype": "Shopee Push Mechanism Logs",
            "push_type": type(req),
            "push_msg": json.dumps(req),
            "data_fetched": (req['code'] == ORDER_PUSH),
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()

    # if(req['code'] == 0):
    if(True):
        # TODO: iterate through all items in list and obtain item numbers (separate from order number)
        all_order_item_dict = []
        # _TODO: create sales order and update all details
        
        add_new_so = frappe.get_doc(
            {
                "doctype": "Sales Order",
                "naming_series": "SAL-ORD-.YYYY.-",
                "customer": "Luiz Practice Customer",
                "order_type": "Sales",
                "transaction_date": str(date.today()),
                "delivery_date": str(date.today() + timedelta(days=7)),
                "company": "Nature to Nurture",
                "currency": "PHP",
                "conversion_rate": 50.50,
                "selling_price_list": "Standard Selling",
                "plc_conversion_rate": 75.50,
                "set_warehouse": "Store - Shopee - NTN",
                "order_number": str(randint(0,9999999999)),
                "shopping_platform": "Shopee",
                "items": [
                    {
                        "item_code": "SAMPLECODE101",
                        "item_name": "Practice API Item 1",
                        "description": "Just a practice description using API",
                        "qty": 3,
                        "uom": "kg",
                        "conversion_factor": 1,
                        "price_list_rate": "700.00",
                        "rate": "700.00",
                        "amount": "2,100.00",
                        "stock_uom_rate": "700.00",
                        "net_rate": "600.00",
                        "net_amount": "1,800.00",
                        "billed_amt": "2,100.00",
                        "valuation_rate": "500.00",
                        "gross_profit": "600.00",
                        "projected_qty": 31,
                        "actual_qty": 42,
                    }
                ],
                "status": "To Deliver and Bill"
            }
            # omitted above
            # "order_item_number": str(all_order_item_id),
        )
        add_new_so.insert(ignore_permissions=True)
        frappe.db.commit()

    elif(req['code'] == ORDER_PUSH):
        status = req['data']['status']
        if(status == 'UNPAID'): 
            # TODO: iterate through all items in list and obtain item numbers (separate from order number)
            all_order_item_dict = []
            # _TODO: create sales order and update all details
            add_new_so = frappe.get_doc(
                {
                    "doctype": "Sales Order",
                    "naming_series": "SAL-ORD-.YYYY.-",
                    "customer": "Luiz Practice Customer",
                    "order_type": "Sales",
                    "transaction_date": str(date.today()),
                    "delivery_date": str(date.today() + timedelta(days=7)),
                    "company": "Nature to Nurture",
                    "currency": "PHP",
                    "conversion_rate": 50.50,
                    "selling_price_list": "Standard Selling",
                    "plc_conversion_rate": 75.50,
                    "set_warehouse": "Store - Shopee - NTN",
                    "order_number": req['data']['ordersn'],
                    
                    "shopping_platform": "Shopee",
                    "items": all_order_item_dict,
                    "status": "To Deliver and Bill",
                }
                # omitted above
                # "order_item_number": str(all_order_item_id),
            )
            add_new_so.insert(ignore_permissions=True)
            frappe.db.commit()
        elif(status == 'READY_TO_SHIP'):
            # orders = get_order(req['data']['ordersn'])
            # return insert_into_frappe(orders)
            pass
        elif(status == 'PROCESSED'):
            pass
        elif(status == 'SHIPPED'):
            pass
        elif(status == 'RETRY_SHIP'):
            pass
        elif(status == 'TO_CONFIRM_RECEIVE'):
            pass
        elif(status == 'IN_CANCEL'):
            pass
        elif(status == 'CANCELLED'):
            pass
        elif(status == 'TO_RETURN'):
            pass
        elif(status == 'COMPLETED'):
            pass
    
    return dict(
        status_code=200, body="Succeeded!"
    )


@frappe.whitelist(allow_guest=True)
def get_order_list(sandbox=False):
    path = "/api/v2/order/get_order_list"
    access_token, timestamp,  partner_id, shop_id, partner_key = get_common_params(
        sandbox=sandbox
    )
    params = {
        "access_token": access_token,
        "timestamp": timestamp,
        "partner_id": partner_id,
        "shop_id": shop_id,
        "time_range_field": "create_time",
        "time_from": 1706773745,
        "time_to": 1706865058,
        "page_size": 50,
        "order_status": "UNPAID"
    }
    temp_base_string = "%s%s%s%s%s" % (
        partner_id,
        path,
        timestamp,
        access_token,
        shop_id,
    )
    params["sign"] = get_sign(partner_key, temp_base_string)
    url = HOST_SB if sandbox else HOST
    res = requests.get(url + path, params=params, allow_redirects=False)

    #print(res['response'])
    #restest = requests.get(res.url,headers=headers, data=payload, allow_redirects=False)
    save_scratch_data(res.url, "order url")
    res = json.loads(res.text)
    save_scratch_data(res, "order details")
    print(res)
    return res['response']


@frappe.whitelist(allow_guest=True)
def ship_order(order_id, sandbox=False):
    # get shipment list
    # get order detail
    # TODO: remove temporary return below
    # return
    sandbox = sandbox == True
    details = get_order(order_id, sandbox=sandbox)
    save_scratch_data(details, "package list")
    order = details.pop(0)
    order = order["package_list"].pop(0)

    package_number = order["package_number"]
    # get shipping parameter ; select which mode to use here: pickup
    shipping_parameters = get_shipping_parameter(order_id, sandbox=sandbox)
    # ship order
    save_scratch_data(shipping_parameters, "test-")
    if shipping_parameters:
       pickup_loc = shipping_parameters["pickup"]["address_list"]
       ship_params = {
           "package_number": package_number,
           "address_id": pickup_loc["address_id"],
           "pickup_time_id": pickup_loc["time_slot_list"].pop(0)["pickup_time_id"],
       }
       shipping = ship_package(order_id, shipping_params=ship_params, sandbox=sandbox)

       tracking_num = get_tracking_number(order_id, ship_params, sandbox=sandbox)
       document_params = get_shipping_document_parameters(
        order_id, ship_params, sandbox=sandbox
       )
       shipping_document = create_shipping_document(
           order_id, tracking_num, ship_params, sandbox=sandbox
       )
       pass

# ! temporary whitelist
@frappe.whitelist(allow_guest=True)
def get_shipping_parameter(order_id="240202FNFFHX4D", sandbox=False):
    # unpaid order (02-02): 240202GD5WKWN9 or 240202FNFFHX4D
    # to ship order (02-02): 240202G7VE1088
    path = "/api/v2/logistics/get_shipping_parameter"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params(
        sandbox=sandbox
    )
    params = {
        "access_token": access_token,
        "order_sn": order_id,
        "timestamp": timestamp,
        "partner_id": partner_id,
        "shop_id": shop_id,
    }
    temp_base_string = "%s%s%s%s%s" % (
        partner_id,
        path,
        timestamp,
        access_token,
        shop_id,
    )

    params["sign"] = get_sign(partner_key, temp_base_string)
    url = HOST_SB if sandbox else HOST
    res = requests.get(url + path, params=params)
    print(res)
    res = json.loads(res.content)
    save_scratch_data(res, "shipping params from TEMP")
    return res["response"]

# generated by ChatGPT-4
@frappe.whitelist(allow_guest=True)
def get_common_delivery_dates(sales_order_names="['SAL-ORD-2024-00974','SAL-ORD-2024-00057']"):
    """
    Gets all common delivery dates for all selected sales orders and returns either of the ff:
    - a dict (free=False) and dates: [list of allowed dates in (str?) format]
    - a dict (free=False) and dates: []     --> no available date
    - a dict (free=True)                    --> all dates are available (no restriction)  
    """
    avail_dates = None
    free = True
    sales_order_names = sales_order_names.strip('][').replace("'","").replace("\"","").split(',')
    save_scratch_data(sales_order_names, "selected sales orders, pending batch update of delivery date")
    for an_so in sales_order_names:
        an_so = frappe.get_doc("Sales Order", an_so).as_dict()
        print(an_so["shopping_platform"])
        if an_so["shopping_platform"]=="Shopee":
            free = False                                            # there will be a range of allowed dates
            # TODO: configure the parsed date format!
            so_allowed_dates = an_so["delivery_date_allowed"].strip('][').replace("'","").split(', ')
            so_allowed_dates = set(so_allowed_dates)
            if avail_dates is None:
                avail_dates = so_allowed_dates
            else:
                avail_dates.intersection_update(so_allowed_dates)
            print(avail_dates)

    save_scratch_data(avail_dates, "COMMON DELIVERY DATE from batch update of delivery date")
    avail_dates = list() if avail_dates is None else list(avail_dates)

    return dict(
        free=free,
        avail_dates=avail_dates,
        none_value=None
    )

# generated by ChatGPT-4
@frappe.whitelist(allow_guest=True)
def update_sales_orders_delivery_date(sales_order_names, delivery_date):
    for name in sales_order_names:
        doc = frappe.get_doc("Sales Order", name)
        doc.delivery_date = delivery_date
        doc.save()
    frappe.db.commit()  # Ensure changes are saved to the database


def ship_package(order_id, shipping_params, sandbox=False):
    path = "/api/v2/logistics/ship_order"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params(
        sandbox=sandbox
    )
    params = {
        "access_token": access_token,
        "timestamp": timestamp,
        "partner_id": partner_id,
        "shop_id": shop_id,
    }
    temp_base_string = "%s%s%s%s%s" % (
        partner_id,
        path,
        timestamp,
        access_token,
        shop_id,
    )

    params["sign"] = get_sign(partner_key, temp_base_string)
    payload = {
        "order_sn": order_id,
        # 'package_number' : ,
        "pickup": {
            "address_id": shipping_params["address_id"],  # change to be dynamic
            "pickup_time_id": shipping_params["pickup_time_id"],  # change to be dynamic
        },
    }
    url = HOST_SB if sandbox else HOST
    res = requests.post(url + path, params=params, json=payload)
    res = json.loads(res.content)
    save_scratch_data(res, "ship package")
    return res


def get_tracking_number(order_id, shipping_params, sandbox=False):
    path = "/api/v2/logistics/get_tracking_number"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params(
        sandbox=sandbox
    )
    params = {
        "access_token": access_token,
        "order_sn": order_id,
        "timestamp": timestamp,
        "partner_id": partner_id,
        "shop_id": shop_id,
        "package_number": shipping_params["package_number"],
    }
    temp_base_string = "%s%s%s%s%s" % (
        partner_id,
        path,
        timestamp,
        access_token,
        shop_id,
    )

    params["sign"] = get_sign(partner_key, temp_base_string)
    url = HOST_SB if sandbox else HOST
    res = requests.get(url + path, params=params)
    res = json.loads(res.content)
    save_scratch_data(res, "get tracking number")
    return res["response"]["tracking_number"]


@frappe.whitelist(allow_guest=True)
def get_waybill(order_id, sandbox=False):
    frappe.msgprint(order_id)
    sandbox = sandbox == True
    package_number = get_order(order_id).pop(0)["package_list"].pop(0)["package_number"]
    ship_params = {"package_number": package_number}

    tracking_num = get_tracking_number(order_id, ship_params, sandbox=sandbox)
    # if tracking_num == '':
    #     save_scratch_data('no tracking num', 'no tracking num')
    #     return {'message' : 'Waybill not yet ready'}

    document_params = get_shipping_document_parameters(
        order_id, ship_params, sandbox=sandbox
    )
    shipping_document = create_shipping_document(
        order_id, tracking_num, ship_params, sandbox=sandbox
    )

    rdy = get_shipping_document_result(order_id, ship_params, sandbox=sandbox)
    try:
        if rdy["response"]["result_list"].pop(0)["status"] != "READY":
            return {"status_code": 400, "message": "Waybill not yet ready"}
    except KeyError:
        pass
    res = download_shipping_document(order_id, ship_params)
    return {
        "status_code": 200,
        "message": "Waybill Ready",
        "file": res.content,
    }


def get_shipping_document_parameters(order_id, shipping_params, sandbox=True):
    save_scratch_data(shipping_params["package_number"], "shipping-params")
    path = "/api/v2/logistics/get_shipping_document_parameter"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params(
        sandbox=sandbox
    )
    params = {
        "access_token": access_token,
        "timestamp": timestamp,
        "partner_id": partner_id,
        "shop_id": shop_id,
    }
    temp_base_string = "%s%s%s%s%s" % (
        partner_id,
        path,
        timestamp,
        access_token,
        shop_id,
    )

    payload = {
        "order_list": [
            {
                "order_sn": order_id,
                "package_number": "",
            }
        ],
    }
    params["sign"] = get_sign(partner_key, temp_base_string)
    url = HOST_SB if sandbox else HOST
    res = requests.post(url + path, params=params, json=payload)
    res = json.loads(res.content)
    
    save_scratch_data(res, "shipping document params")
    return res["response"]["result_list"]


def create_shipping_document(order_id, tracking_num, shipping_params, sandbox=True):
    frappe.msgprint(shipping_params)
    path = "/api/v2/logistics/create_shipping_document"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params(
        sandbox=sandbox
    )
    params = {
        "access_token": access_token,
        "timestamp": timestamp,
        "partner_id": partner_id,
        "shop_id": shop_id,
    }
    temp_base_string = "%s%s%s%s%s" % (
        partner_id,
        path,
        timestamp,
        access_token,
        shop_id,
    )

    params["sign"] = get_sign(partner_key, temp_base_string)

    payload = {
        "order_list": [
            {
                "order_sn": order_id,
                "package_number": shipping_params["package_number"],
                "tracking_number": tracking_num,
                'shipping_document_type' : None,
            }
        ]
    }
    url = HOST_SB if sandbox else HOST
    res = requests.post(url + path, params=params, json=payload)
    save_scratch_data(res, "test")
    res = json.loads(res.content)
    save_scratch_data(res, "shipping document")
    return res["response"]


def get_shipping_document_result(order_id, shipping_params, sandbox=True):
    path = "/api/v2/logistics/get_shipping_document_result"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params(
        sandbox=sandbox
    )
    params = {
        "access_token": access_token,
        "timestamp": timestamp,
        "partner_id": partner_id,
        "shop_id": shop_id,
    }
    temp_base_string = "%s%s%s%s%s" % (
        partner_id,
        path,
        timestamp,
        access_token,
        shop_id,
    )

    params["sign"] = get_sign(partner_key, temp_base_string)

    payload = {
        "order_list": [
            {
                "order_sn": order_id,
                "package_number": shipping_params["package_number"],
                # 'shipping_document_type' : None,
            }
        ]
    }
    url = HOST_SB if sandbox else HOST
    res = requests.post(url + path, params=params, json=payload)
    res = json.loads(res.content)
    save_scratch_data(res, "shipping document result")
    if res["error"] != "":
        return res["response"]
    else:
        return res


def download_shipping_document(order_id, shipping_params, sandbox=True):
    path = "/api/v2/logistics/download_shipping_document"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params(
        sandbox=sandbox
    )
    params = {
        "access_token": access_token,
        "timestamp": timestamp,
        "partner_id": partner_id,
        "shop_id": shop_id,
    }
    temp_base_string = "%s%s%s%s%s" % (
        partner_id,
        path,
        timestamp,
        access_token,
        shop_id,
    )

    params["sign"] = get_sign(partner_key, temp_base_string)

    payload = {
        "order_list": [
            {
                "order_sn": order_id,
                "package_number": shipping_params["package_number"],
            }
        ]
    }
    url = HOST_SB if sandbox else HOST
    res = requests.post(url + path, params=params, json=payload)
    # res = json.loads(res.content)
    save_scratch_data(res.content, "waybill file")
    return res


@frappe.whitelist(allow_guest=True)
def lazada_order_pack(req_params):
    """
    For Shopee, oncreate of delivery note, set status to READY_TO_SHIP
    """
    # req_params_json = json.loads(req_params)
    # client = LazopClient(url, appkey, appSecret)
    # request = LazopRequest("/order/pack")
    # request.add_api_param("shipping_provider", req_params_json["shipping_provider"])
    # request.add_api_param("delivery_type", req_params_json["delivery_type"])
    # request.add_api_param("order_item_ids", req_params_json["order_item_ids"])
    # response = client.execute(request, access_token)

    add_item = frappe.get_doc(
        {
            "doctype": "Shopee Push Mechanism Logs",
            "push_type": "Manual Pack Update",
            "push_msg": "json.dumps(response.body)",
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()

    return add_item