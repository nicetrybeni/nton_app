import frappe
import hmac
import json
from frappe import ValidationError
from erpnext import get_default_company
import time
import requests
import hashlib
from datetime import datetime, date, timedelta
import urllib.parse
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice, make_delivery_note
from erpnext.accounts.doctype.payment_request.payment_request import (
    make_payment_request,
    make_payment_entry,
)
from erpnext.stock.utils import get_stock_balance


# DOMAIN = "https://open-api-sandbox.tiktokglobalshop.com"
DOMAIN = "https://open-api.tiktokglobalshop.com"

# DOMAIN = "https://auth-sandbox.tiktok-shops.com"
# DOMAIN = "https://auth.tiktok-shops.com"
VERSION = "202309"
ORDER_STATUS_CHANGE = 1
REVERSE_STATUS_UPDATE = 2
RECIPIENT_ADDRESS_UPDATE = 3
PACKAGE_UPDATE = 4
PRODUCT_STATUS_CHANGE = 5
SELLER_DEAUTHORIZATION = 6
AUTH_EXPIRE = 7
CANCELLATION_STATUS_CHANGE = 11
RETURN_STATUS_CHANGE = 12
APP_KEY = "6a8u5auuqugdu"
APP_SECRET = "cfa8480cdb0288ead599611f2e4fcaf95dfe3616"
# SHOP_CIPHER = "ROW_kRDV4AAAAABYJ9g3O028TW8hELLXysK-"
SHOP_CIPHER = "ROW_e0BrjAAAAAD1Gw5QSHlOOAspT9BRLNt_"
# SHOP_ID = "GBLCBLWLWS"
SHOP_ID = "PHLCG2WLYS"
default_company = frappe.get_doc("Company", get_default_company()).as_dict()

def unix_to_datetime(unix):
    unix = int(unix) // 1000
    NUM_OF_SEC_IN_DAYS = 86400
    return frappe.utils.add_days(
        frappe.utils.get_datetime("1970-01-01"), (unix) / NUM_OF_SEC_IN_DAYS
    )


@frappe.whitelist(allow_guest=True)
def tiktok_webhook(req_temp=None):
    try:
        req = json.loads(frappe.request.data.decode('utf-8'))
    except:
        try:
            req = json.loads(req_temp)
        except:
            save_scratch_data(req, "error webhook - can't process input")
            return dict(
                status=400,
                message="error webhook - can't process input"
            )
    
    try:
        save_scratch_data(req, "live webhook webhook")
        
        if req["type"] == ORDER_STATUS_CHANGE:
                # SO -> DN -> SI
                # check for waybill generation (url)
            status = req["data"]["order_status"]
            if status == "UNPAID":
                # 
                # return get_orders(req)
                save_scratch_data(req, "UNPAID webhook")
                # return get_orders(req)
                # pass  # 1h waiting period
            elif status == "AWAITING_SHIPMENT":
                # return get_orders(req)
                save_scratch_data(req, "AWAITING_SHIPMENT webhook")
                return get_orders(req)
            elif status == "AWAITING_COLLECTION":
                # TODO: call function to create the delivery note
                return ship_order_new(req)
            elif status == "CANCEL":
                pass
            elif status == "IN_TRANSIT":
                pass
            elif status == "DELIVERED":
                save_scratch_data(req, "delivered webhook")
                pass
            elif status == "COMPLETED":
                pass

        elif req["type"] == REVERSE_STATUS_UPDATE:
            pass
        elif req["type"] == RECIPIENT_ADDRESS_UPDATE:
            pass
        elif req["type"] == PACKAGE_UPDATE:
            pass
        elif req["type"] == PRODUCT_STATUS_CHANGE:
            pass
        elif req["type"] == SELLER_DEAUTHORIZATION:
            pass
        elif req["type"] == AUTH_EXPIRE:
            pass
        elif req["type"] == CANCELLATION_STATUS_CHANGE:
            pass
        elif req["type"] == RETURN_STATUS_CHANGE:
            pass
        return 200
    except Exception as e:
        return dict(
            status=400,
            message="Error in webhook: " + str(e)
        )


@frappe.whitelist(allow_guest=True)
def tiktok_webhook_sb():
    # handle different webhook cases
    req = json.loads(frappe.request.data.decode('utf-8'))

    # doc = frappe.get_doc({
    #     'doctype' : 'Tiktok Webhook',
    #     'content' : str(req['data'])
    # })
    # doc.insert()
    # frappe.db.commit()
    if req["type"] == ORDER_STATUS_CHANGE:
            # SO -> DN -> SI
            # check for waybill generation (url)
        status = req["data"]["order_status"]
        if status == "UNPAID":
            # 
            # return get_orders(req)
            save_scratch_data(req, "UNPAID webhook")
            return get_orders(req)
            # pass  # 1h waiting period
        elif status == "AWAITING_SHIPMENT":
            # return get_orders(req)
            save_scratch_data(req, "AWAITING_SHIPMENT webhook")
            return get_orders(req)
        elif status == "CANCEL":
            pass
        elif status == "IN_TRANSIT":
            pass
        elif status == "DELIVERED":
            save_scratch_data(req, "delivered webhook")
            pass
        elif status == "COMPLETED":
            pass

    elif req["type"] == REVERSE_STATUS_UPDATE:
        pass
    elif req["type"] == RECIPIENT_ADDRESS_UPDATE:
        pass
    elif req["type"] == PACKAGE_UPDATE:
        pass
    elif req["type"] == PRODUCT_STATUS_CHANGE:
        pass
    elif req["type"] == SELLER_DEAUTHORIZATION:
        pass
    elif req["type"] == AUTH_EXPIRE:
        pass
    elif req["type"] == CANCELLATION_STATUS_CHANGE:
        pass
    elif req["type"] == RETURN_STATUS_CHANGE:
        pass

    return 200
    
    
def save_scratch_data(data, tags):
    doc = frappe.get_doc(
        {"doctype": "Tiktok Webhook", "content": str(data), "tags": str(tags)}
    )
    doc.insert()
    frappe.db.commit()


# @frappe.whitelist(allow_guest=True)
def get_orders(req):
    order_id = req["data"]["order_id"]
    # get_order_detail
    # order list
    # payment info
    order_list = get_order_details(order_id)
    save_scratch_data(req, "get Order")
    
    return insert_order_to_frappe(order_list)


def insert_order_to_frappe(order_list):
    sales_order = {"doctype": "Sales Order"}
    # abbr = frappe.get_all("Company", filters={"fieldname": "TIKTOK"}, fields=['*'])
    # if order_list is not None:
    #     save_scratch_data(order_list, "order_list webhook")
    # else:
    #     save_scratch_data("Empty order list", "order_list webhook")
        
    # default_company = frappe.db.get_value("Company", get_default_company(), "abbr")
    

    # save_scratch_data(order_list,'order list')
    item_frappe = []  # item_code, deliveyr date, qty, rate
    for order in order_list["data"]["order_list"]:
        # 1 order -> 1 sales order
        sales_order["customer"] = frappe.get_doc(
            "Customer", "Tiktok Customer"
        ).name  # does not matter
        sales_order["customer_name"] = order["buyer_uid"]
        sales_order["transaction_date"] = unix_to_datetime(order["create_time"])
        sales_order["delivery_date"] = frappe.utils.add_days(
            sales_order["transaction_date"], 7
        )
        sales_order["company"] = "Nature to Nurture"  # does not matter
        sales_order["shopping_platform"] = "Tiktok"
        sales_order["order_number"] = order["order_id"]
        sales_order["set_warehouse"] = frappe.get_doc(
            "Warehouse", f"Store - Tiktok - {default_company['abbr']}"
        ).name
        for item_tiktok in order["item_list"]:
            # 1 item -> 1 row in sales order
            item_single = {"doctype": "Sales Order Item"}

            item_single["item_code"] = item_tiktok["seller_sku"]  # Frappe -> Tiktok
            item_single["qty"] = item_tiktok["quantity"]
            # sales_order["discount_amount"] = item_tiktok['sku_seller_discount'] #new modification 1/25/24
            item_single["price_list_rate"] = item_tiktok["sku_sale_price"]
            item_frappe.append(item_single)
            # TODO: Deal with discounts

        sales_order["items"] = item_frappe
        # save_scratch_data(sales_order, "sales order")
        doc = frappe.get_doc(sales_order)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
    return {"status_code": 200}


def get_order_details(order_id):
    path = "/api/orders/detail/query"
    params = get_common_params()
    params["shop_id"] = SHOP_ID

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)

    order_list = [order_id]
    data = {"order_id_list": order_list}

    res = requests.post(DOMAIN + path, params=params, json=data)
    order_list = json.loads(res.content)
    # save_scratch_data(order_list, 'order_details')
    return order_list


###########################################
# SHIP ORDER FLOW
# called after submitting Delivery Note
# get order_id
# get order detail -> get package_id
# ship package_id
# get_shipping_document : shop_id order_id


# ! NEW: auto-create delivery note
@frappe.whitelist(allow_guest=True)
def ship_order_new(req):
    """
    Calls the helper function to create the delivery note of the sales order (happens when the order is marked as Shipped / To Ship Out)
    - req: parsed JSON object from webhook object
    """
    url = "https://naturetonurture.rayasolutions.store/api/method/"
    path = "nton_app.tiktokshop_api.ship_order_new_helper"
    headers = {
        "Authorization": "Token e2624ee0eba9640:38ecfa3de786d24",
        "Content-Type": "application/json"
    }
    payload = {
        "order_id": req["data"]["order_id"]
    }
    params = {
        
    }
    res = requests.post(url + path, headers=headers, params=params, json=payload)
    # parameters of ship_order_new_helper must be in payload object (where json=payload) to insert parameters correctly 
    res = json.loads(res.content)
    return res

@frappe.whitelist(allow_guest=True)
def ship_order_new_helper(order_id="ADSFJKDLSGJSDLFKSDORF123", sandbox=False):
    """
    Holds the actual implementation of creating a new delivery note.
    """
    print("order_id:", order_id)
    existing_so = frappe.db.sql(
        f"SELECT name,customer,shopping_platform FROM `tabSales Order` WHERE order_number='{order_id}';",
        as_dict=True
    )
    
    if not existing_so:     # sales order not found; throw an error!
        save_scratch_data("No sales order found!","error ship_order_new")
        return dict(
            status=400,
            message="error - TikTok pushmech order_status (No Sales Order found!)"
        )
    
    # submit the sales order and create the delivery note
    try:
        existing_so_fetched = frappe.get_doc("Sales Order", existing_so[0].name)
        existing_so_fetched_dict = existing_so_fetched.as_dict()
        existing_so_fetched.save(ignore_permissions=True)
        if existing_so_fetched_dict["docstatus"]==0:
            existing_so_fetched.submit()
        
        if existing_so_fetched_dict["delivery_status"]!="Not Delivered": # ! assume that the delivery notes are submitted for the whole order (not per item)
            raise Exception("TIKTOK API - The current sales order already has a bound delivery note!")
        
        """
        new_dn = make_delivery_note(existing_so[0].name)
        new_dn.shipping_status = ""
        new_dn.insert()
        frappe.db.commit()

        new_dn.save()
        new_dn.submit()
        """
        
        new_dn = make_delivery_note(existing_so[0].name)
        # new_dn = existing_so_fetched.make_delivery_note()
        new_dn.shipping_status = ""
        # new_dn.insert()
        # frappe.db.commit()
        # ? insert() and commit() were not commented until inspection_required changes were added
        new_dn_dict = new_dn.as_dict()

        # iterate through the items...
        for an_item in new_dn_dict["items"]:
            an_item_doc = frappe.get_doc("Item", an_item["item_code"])
            print("an_item_doc.inspection_required_before_delivery:",an_item_doc.inspection_required_before_delivery)
            if an_item_doc.inspection_required_before_delivery:
                auto_submit = False
                break
        
        # new_dn.insert()
        # frappe.db.commit()

        new_dn.save()
        # # check if Item's inspection_required_before_delivery is checked. If yes, do NOT submit first...
        if auto_submit:
            new_dn.submit()

    except Exception as e:
        save_scratch_data(str(e),"error TikTok (TRY/EXCEPT block) - pushmech order_status packed")
        return dict(
            status=400,
            message=f"TikTok error (TRY/EXCEPT block) - {str(e)}"
        )
    else:
        # Ensure that permission checks are restored to their original state
        return dict(
            status=200,
            message="Finished TikTok shipping process!"
        )

@frappe.whitelist(allow_guest=True)
def ship_order(order_id):
  
    package_ids = get_package_id(order_id)
    
    if package_ids:
        package_id = package_ids.pop(0)
        package_details = get_package_detail(package_id)
        shipping = ship_package(package_details) #issue: 'message': 'Internal system error. Please try again later.'
        get_shipping_timeslot(package_id=package_id) # issue: 'message': 'System timeout'
        
        get_shipping_info(package_id=package_id)
        get_shipping_information(order_id=order_id)
        # waybill = get_waybill(order_id)
        # ship package_id
        # TODO:
        # Seller does drop-off or pick-up - pick up
        # if shipping["message"] == "Success":
        #     return {"status_code": 200}
        # else:
        #     return {"status_code": 400}
        return shipping
    else:
        frappe.msgprint("No Available Item to ")
        
def get_package_id(order_id):
    path = "/api/orders/detail/query"
    params = get_common_params()
    params["shop_id"] = SHOP_ID
    
    try:
        url = requests.get(DOMAIN + path, params=params).url
        # save_scratch_data(url,'url')
        params["sign"] = generate_sign(secret=APP_SECRET, url=url)

        body = {"order_id_list": [order_id]}
        
        # save_scratch_data(params,'order_params')
        res = requests.post(DOMAIN + path, params=params, json=body)
        order_detail = json.loads(res.content)

        # save_scratch_data(order_detail,'order_detail')
        package_ids = []
        for order in order_detail["data"]["order_list"]:
            for package_list in order["package_list"]:
                package_ids.append(package_list["package_id"])
                # save_scratch_data(package_list, "package_list")
       
        
        return package_ids
    except Exception as e:
         save_scratch_data("Somthing went wrong", "package_ids")
        


def get_package_detail(package_id):
    path = "/api/fulfillment/detail"
    params = get_common_params()
    params["shop_id"] = SHOP_ID
    params["package_id"] = package_id

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)

    res = requests.get(DOMAIN + path, params=params)
    res = json.loads(res.content)
    
   
    # save_scratch_data(res,'package_details')
    # pick up start and end
    # tracking num, shipping provider id
    details = res["data"]
    save_scratch_data(details, "Shipping package fulfillment details")
    package_details = {
        # 'shipping_provider_id' : details['shipping_provider_id'],
        # 'tracking_number' : details['tracking_number'],
        "package_id": details["package_id"]
    }
    return package_details


def get_shipping_timeslot(package_id):
    path = "/api/fulfillment/package_pickup_config/list"
    params = get_common_params()
    params["shop_id"] = SHOP_ID
    params["package_id"] = package_id

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)

    res = requests.get(DOMAIN + path, params=params)
    res = json.loads(res.content)

    save_scratch_data(res, "shipping_timeslots")
    # pick up start and end
    # tracking num, shipping provider id
    # details = res['data']['pickup_time_list']
    # start_time = details[0]['start_time']
    # end_time = details[0]['end_time']
    # timeslots = {
    #     'start_time' : start_time,
    #     'end_time' : end_time
    # }
    return res


def get_shipping_info(package_id):
    path = "/api/fulfillment/shipping_info"
    params = get_common_params()
    params["shop_id"] = SHOP_ID
    params["package_id"] = package_id

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)

    res = requests.get(DOMAIN + path, params=params)
    res = json.loads(res.content)
    save_scratch_data(res, "get_shipping_info")
    
    return res


def ship_package(package_details):
    path = "/api/fulfillment/rts"
    params = get_common_params()
    params["shop_id"] = SHOP_ID

    # self_shipment = {
    #     'tracking_number' : package_details['tracking_number'],
    #     'shipping_provider_id' : package_details['shipping_provider_id']
    # }

    body = {"package_id": package_details["package_id"], "pick_up_type": 1}

    params["shop_id"] = SHOP_ID

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)

    res = requests.post(DOMAIN + path, params=params, json=body)
    res = json.loads(res.content)
        
    # if res.get("message") != "success":
    #  # If the message is not "success", raise an exception or handle it as needed.
    #     raise Exception(f"Failed to ship package. Message: {res.get('message')}")
    
    save_scratch_data(res, "shipped package")

    return res


def get_shipping_information(order_id):
    path = "/api/logistics/ship/get"
    params = get_common_params()
    params["shop_id"] = SHOP_ID
    params["order_id"] = order_id

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)

    res = requests.get(DOMAIN + path, params=params)
    res = json.loads(res.content)

    save_scratch_data(res, "shipping_information")
    return res


@frappe.whitelist(allow_guest=True)
def get_waybill(order_id):
    path = "/api/logistics/shipping_document"
    params = get_common_params()

    params["shop_id"] = SHOP_ID
    params["order_id"] = order_id
    params["document_type"] = "SL_PL"  # or SHIPPING_LABEL , PICKING_LIST

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)

    res = requests.get(DOMAIN + path, params=params)
    res = json.loads(res.content)
    save_scratch_data(res, "waybill")
    return res["data"]["doc_url"]


@frappe.whitelist(allow_guest=True)
def insert_product(item):
    item = json.loads(item)

    # attributes = []
    # attribute_details = get_item_attribute_form(item['category_id'])
    # attribute_name_to_id = {} # mapping of attrib name : attrib id
    # attribute_value_name_to_id = {}
    # for attribute in attribute_details:
    #     attrib_name = attribute['attribute_name']
    #     attrib_id = attribute['attribute_id']
    #     attribute_name_to_id[attrib_name] = attrib_id

    #     attribute_value_name_to_id[attrib_name] = dict(zip(attribute['values_name'], attribute['values_id']))
    # use case: attribute_value_name_to_id[attribute_name] -> get mapping of value to id PER attribute
    #           attribute_value_name_to_id[attribute_name][attribute_value] -> id of attribute value

    # get id of attrib
    # get id of value
    # attribute { attrib_id , value_id }
    save_scratch_data(item, "item")
    # for attribute in item['item_attributes']:
    #     builder = {}
    #     builder['attribute_id'] = attribute_name_to_id[attribute['attrib_name']]

    #     if(attribute['attrib_value'] == 'Enter custom value'):
    #         builder['custom_value'] = 'Custom'
    #     else:
    #         builder['value_id'] = attribute_value_name_to_id[attribute['attrib_name']][attribute['attrib_value']]

    #     attributes.append(builder)
    # save_scratch_data(attributes, 'item_attributes')

    # s_attributes = attributes
    # p_attributes = attributes

    # if(len(attributes) > 3):
    #     s_attributes = attributes[0:2]

    # default_company = frappe.get_doc("Company", get_default_company()).as_dict()
    wh = frappe.get_doc("Warehouse", f"Store - Tiktok - {default_company['abbr']}").name
    # it = frappe.get_doc('Item', item['item_name']).name
    # save_scratch_data(it, 'wh name')
    it = frappe.get_doc("Item", item["item_code"]).name
    # save_scratch_data(it, 'wh name')
    # stock = get_stock_balance(item['item_name'], wh)
    # save_scratch_data(stock,'stock2')

    stock = get_stock_balance(it, wh)
    save_scratch_data(stock, "stock1")

    item["stock"] = int(stock)
    sku = [
        {
            "seller_sku": item["item_code"],
            "original_price": str(item["tiktok_selling_price"]),
            "stock_infos": [
                {"warehouse_id": item["warehouse_id"], "available_stock": int(stock)}
            ],
            #     'sales_attributes' : s_attributes,
        }
    ]

    # image = upload_img()
    # images = [image]
    # images.append(image)
    body = {
        "category_id": item["category_id"],
        # 'description' : item['description'],
        # 'images' : images,
        # 'package_height' : item['package_height'],
        # 'package_length' : item['package_length'],
        # 'package_weight' : item['package_weight'],
        # 'package_width' : item['package_width'],
        "product_name": item["item_name"],
        "skus": sku,
        # 'product_attributes' : p_attributes,
        # 'is_cod_open': (item['is_cod'] == '1'),
        # 'exemption_of_identifier_code': {
        # 'exemption_reason': [
        # 1,
        # ],
        # },
    }
    path = ""
    if is_json_key_present(item, "item_id"):
        if item["item_id"]:
            body["product_id"] = item["item_id"]
            # path = '/api/products'
    else:
        body["product_id"] = None
        path = "/api/products/save_draft"
    save_scratch_data(body, "product info")

    params = get_common_params()
    params["shop_id"] = SHOP_ID

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)
    res = ""
    save_scratch_data(body, "item info")
    if body["product_id"] is None:  # draft
        try:
            res = requests.post(DOMAIN + path, params=params, json=body)
            res = json.loads(res.content)
            save_scratch_data(res.content, "draft product")
        except Exception as e:
            save_scratch_data(e, "error d")
    else:  # update stock and price
        try:
            # res = requests.put(DOMAIN+path, params=params, json=body)
            res_s = update_stock(item)
            res_p = update_price(item)
            res = str(res_p) + str(res_s)  # TODO: TESTING THIS
            save_scratch_data(res, "upd product")
        except Exception as e:
            save_scratch_data(e, "error u")

    return res


def update_stock(item):
    path = "/api/products/stocks"
    params = get_common_params()
    params["shop_id"] = SHOP_ID

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)
    body = {
        "product_id": item["item_id"],
        "skus": [
            {
                "id": item["sku_id"],
                "stock_infos": [
                    {
                        "warehouse_id": item["warehouse_id"],
                        "available_stock": int(item["stock"]),
                    }
                ],
                #     'sales_attributes' : s_attributes,
            }
        ],
    }
    res = requests.put(DOMAIN + path, params=params, json=body)
    res = json.loads(res.content)
    save_scratch_data(res, "update stock")
    return res


def update_price(item):
    path = "/api/products/prices"
    params = get_common_params()
    params["shop_id"] = SHOP_ID

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)
    body = {
        "product_id": item["item_id"],
        "skus": [
            {
                "id": item["sku_id"],
                "original_price": item["tiktok_selling_price"]
            }
        ],
    }
    # add'l property:    'sales_attributes' : s_attributes,
    res = requests.put(DOMAIN + path, params=params, json=body)
    res = json.loads(res.content)
    save_scratch_data(res, "update price")
    return res


def get_attributes(category_id):
    path = "/api/products/attributes"
    params = get_common_params()
    params["shop_id"] = SHOP_ID
    params["category_id"] = category_id

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)
    res = requests.get(DOMAIN + path, params=params)

    res = json.loads(res.content)
    save_scratch_data(res, "attributes")
    return res["data"]["attributes"]


@frappe.whitelist(allow_guest=True)
def get_mandatory_attributes(category_id):
    attributes = get_attributes(category_id)
    mandatory = []
    for attribute in attributes:
        if attribute["input_type"]["is_mandatory"]:
            mandatory.append(attribute)
    save_scratch_data(mandatory, "attributes2")
    return mandatory


@frappe.whitelist(allow_guest=True)
def get_item_attribute_form(category_id):
    mandatory = get_mandatory_attributes(category_id)
    attribute_details = []
    for attribute in mandatory:
        builder = {}
        builder["attribute_id"] = attribute["id"]
        builder["attribute_name"] = attribute["name"]

        # save_scratch_data(attribute,'attribute check')
        builder["values_id"] = []
        builder["values_name"] = []
        if attribute["input_type"]["is_customized"] == False or is_json_key_present(
            attribute, "values"
        ):
            for value in attribute["values"]:
                builder["values_id"].append(value["id"])
                builder["values_name"].append(value["name"])
        else:
            # builder['values_id'].append('0')
            builder["values_name"].append("Enter custom value")
        # builder['values_id'] = attribute['values']['id'] #array
        # builder['values_name'] = attribute['values']['name'] #array
        attribute_details.append(builder)
    save_scratch_data(attribute_details, "attributes3")
    return attribute_details


def upload_img():
    path = "/api/products/upload_imgs"
    params = get_common_params()
    image = "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"

    params["shop_id"] = SHOP_ID

    body = {"img_data": image, "img_scene": "1"}

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)

    res = requests.post(DOMAIN + path, params=params, json=body)
    res = json.loads(res.content)
    save_scratch_data(res, "image")
    return {"id": res["data"]["img_id"]}


@frappe.whitelist(allow_guest=True)
def get_eligible_categories():
    path = "/api/products/categories"
    params = get_common_params()
    params["shop_id"] = SHOP_ID

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)

    res = requests.get(DOMAIN + path, params=params)
    res = json.loads(res.content)

    # save_scratch_data(res,'categories')
    categories = res["data"]["category_list"]
    eligible_categories = []
    for category in categories:
        if category["is_leaf"] == "True" or category["is_leaf"]:
            eligible_categories.append(category)

    # save_scratch_data(eligible_categories,'cats')
    return eligible_categories


def get_warehouse_list():
    get_cipher()
    path = "/api/logistics/get_warehouse_list"
    params = get_common_params()
    params["shop_id"] = SHOP_ID

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)
    res = requests.get(DOMAIN + path, params=params)

    res = json.loads(res.content)
    save_scratch_data(res, "warehouse")
    # save_scratch_data(params, "params")
    return res["data"]["warehouse_list"]

def get_cipher(version="202212"):
    path = "/api/shop/get_authorized_shop"
    params = {
        "app_key": APP_KEY,
        "timestamp": int(time.time()),
        "sign": None,
        "access_token": get_access_token(),
        "version": version,
    }
    params["shop_id"] = SHOP_ID

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)
    res = requests.get(DOMAIN + path, params=params)

    save_scratch_data(res.json(), "cipher")
    # save_scratch_data(params, "params")
    return res


    
@frappe.whitelist(allow_guest=True)
def get_warehouses():

    warehouses = get_warehouse_list()
    eligible = []
    for warehouse in warehouses:
        if warehouse["warehouse_type"] == 1:
            eligible.append(warehouse)
    return eligible


# set sandbox = true for manual testing
def get_remittance(order_id, sandbox):
    if not sandbox:
        path = "/api/finance/order/settlements"
        params = get_common_params()
        params["shop_id"] = SHOP_ID
        params["order_id"] = order_id

        url = requests.get(DOMAIN + path, params=params).url
        params["sign"] = generate_sign(secret=APP_SECRET, url=url)
        res = requests.get(DOMAIN + path, params=params)
        res = json.loads(res.content)   
    else:
        res = {
            "code": 0,
            "data": {
                "settlement_list": [
                    {
                        "fee_type": "",
                        "product_name": "Nature to Nurture Tongue Cleaner Shop - SAMPLE",
                        "sett_status": 4,
                        "settlement_info": {
                            "affiliate_commission": "0",
                            "affiliate_partner_commission": "0",
                            "charge_back": "100",
                            "currency": "PHP",
                            "customer_service_compensation": "0",
                            "flat_fee": "10",
                            "gst": "100",
                            "logistics_reimbursement": "",
                            "other_adjustment": "0",
                            "payment_fee": "0",
                            "platform_commission": "10",
                            "platform_promotion": "0",
                            "promotion_adjustment": "0",
                            "refund": "0",
                            "refund_subtotal_after_seller_discounts": "100",
                            "sales_fee": "10",
                            "satisfaction_subsidy": "",
                            "settlement_amount": "20",
                            "settlement_time": 1635984000,
                            "sfp_service_fee": "100",
                            "shipping_fee": "100",
                            "shipping_fee_adjustment": "100",
                            "shipping_fee_subsidy": "0",
                            "small_order_fee": "0",
                            "subtotal_after_seller_discounts": "100",
                            "tok_logistics_reimbursement": "",
                            "transaction_fee": "100",
                            "transaction_fee_refund": "",
                            "user_pay": "18000",
                            "vat": "100",
                        },
                        "sku_id": "",
                        "sku_name": "Nature to Nurture Tongue Cleaner Shop",
                        "unique_key": 1637221828875775200,
                    }
                ]
            },
            "message": "Success",
            "request_id": "202203070749000101890810281E8C70B7",
        }
        # save_scratch_data(res, "remittances")
    save_scratch_data(res, "remittances")
    return res["data"]["settlement_list"][0]["settlement_info"]


def get_remittances():
    path = "/api/finance/settlements/search"
    params = get_common_params()
    params["shop_id"] = SHOP_ID

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)
    time_lower_limit = "1666617879"
    # int(time.mktime((datetime.now() - timedelta(days=1)).timetuple()))
    time_upper_limit = "1698153879"
    # int(time.mktime(datetime.now().timetuple()))
    body = {
        "request_time_from": time_lower_limit,
        "request_time_to": time_upper_limit,
        "page_size": 30,
        # 0- sort by trade time, 1- sort by settlement time
    }
    save_scratch_data(body, "remittance time")
    res = requests.post(DOMAIN + path, params=params, json=body)

    res = json.loads(res.content)
    save_scratch_data(res, "remittances")
    return res["data"]


@frappe.whitelist(allow_guest=True)
def bill_remittances(sandbox=False):
    # check corresponding remittance of each sales order
    # get remittances
    # if remittance is paid, create sales invoice

    sales_orders = frappe.db.sql(
        """SELECT name,customer,order_number,total FROM `tabSales Order` WHERE status='To Bill' AND shopping_platform='Tiktok';""",
        as_dict=True,
    )
    
    # query for test cases ( remove if done)
    # sales_orders = frappe.db.sql(
    #     """SELECT name,customer,order_number,total FROM `tabSales Order` WHERE status='To Bill' AND shopping_platform='Tiktok';""",
    #     as_dict=True,
    # )
    
    save_scratch_data(sales_orders, "so")
    for so_single in sales_orders:
        try:
            new_si = make_sales_invoice(so_single["name"], ignore_permissions=True)

            response = get_remittance(so_single["order_number"], sandbox)
            # response = get_remittance("578379050632644769", sandbox)
            save_scratch_data(response, "remittance dummy")
            response_order_json = response

            new_si.insert()

            new_si_fetched = frappe.get_last_doc("Sales Invoice")

            sales_and_tax_single = frappe.new_doc("Sales Taxes and Charges")
            sales_and_tax_single.update(
                {
                    "charge_type": "Actual",
                    # "account_head": "Miscellaneous Expenses - NTN",
                    "account_head": f"Miscellaneous Expenses - {default_company['abbr']}",
                    "description": "Miscellaneous Expenses",
                    # "cost_center": "Main - NTN",
                    "cost_center": f"Main - {default_company['abbr']}",
                    "account_currency": "PHP",
                    # "tax_amount": float(so_single.total)
                    # - float(response_order_json["settlement_amount"]),
                    "tax_amount": float(response_order_json["shipping_fee"]),
                    "parenttype": "Sales Invoice",
                    "parent": new_si_fetched.name,
                    "parentfield": "taxes",
                    "idx": 0,
                }
            )

            sales_and_tax_single.save()
            new_si.taxes.append(sales_and_tax_single)

            new_si.save()
            new_si.submit()
            save_scratch_data(new_si, "SI")

            payment_request = make_payment_request(
                dt="Sales Invoice",
                dn=new_si.name,
                recipient_id="",
                submit_doc=True,
                mute_email=True,
                use_dummy_message=True,
            )
            # https://python.hotexamples.com/site/file?hash=0xfba12d4cbad6378cfbfd55630873d8d617cf5762c27fdc7944e7fb2bc7abf365
            payment_entry = frappe.get_doc(make_payment_entry(payment_request.name))
            payment_entry.submit()
        except KeyError:
            continue

    frappe.db.commit()


@frappe.whitelist(allow_guest=True)
def cron_update_stocks():
    tt_items = frappe.db.sql(
        """SELECT name, tt_item_id, tt_sku_id, tt_warehouse_id FROM `tabItem` WHERE tt_item_id > '';""",
        as_dict=True,
    )
    wh = frappe.get_doc("Warehouse", f"Store - Tiktok - {default_company['abbr']}").name
    # wh = frappe.get_doc("Warehouse", "Store - Tiktok - NTN").name
    save_scratch_data(tt_items, "cron tt update")
    for item_single in tt_items:
        try:
            stock = get_stock_balance(item_single["name"], wh)
            item_details = {
                "item_id": item_single["tt_item_id"],
                "sku_id": item_single["tt_sku_id"],
                "warehouse_id": item_single["tt_warehouse_id"],
                "stock": stock,
            }
            update_stock(item_details)
        except KeyError as e:
            save_scratch_data(e, "tt_cron")
        except Exception as ex:
            save_scratch_data(ex, "tt cron ex")


def get_transactions():
    path = "/api/finance/transactions/search"
    params = get_common_params()
    params["shop_id"] = SHOP_ID

    url = requests.get(DOMAIN + path, params=params).url
    params["sign"] = generate_sign(secret=APP_SECRET, url=url)
    time_lower_limit = "1695535297"
    # int(time.mktime((datetime.now() - timedelta(days=1)).timetuple()))
    time_upper_limit = "1698156098"
    # int(time.mktime(datetime.now().timetuple()))
    body = {
        "request_time_from": time_lower_limit,
        "request_time_to": time_upper_limit,
        "page_size": 30,
        "transaction_type": [2, 3],
        "offset": 0,
        # 0- sort by trade time, 1- sort by settlement time
    }
    res = requests.post(DOMAIN + path, params=params, json=body)

    res = json.loads(res.content)
    save_scratch_data(res, "transactions")
    return res["data"]


def get_common_params(version="202212"):
    return {
        "app_key": APP_KEY,
        "timestamp": int(time.time()),
        "sign": None,
        "access_token": get_access_token(),
        "version": version,
        "shop_cipher": SHOP_CIPHER,
    }


def generate_sign(secret, url):
    scheme, netloc, path, params, _ = urllib.parse.urlsplit(url)
    params = dict(urllib.parse.parse_qsl(params))
    keys = []
    for key in params:
        if key not in ["access_token", "sign"]:
            keys.append(key)
    keys = sorted(keys)
    inp = ""

    for key in keys:
        inp = (
            inp
            + key
            + str(params[key]).replace("[", "").replace("]", "").replace("'", "")
        )

    inp = secret + path + inp + secret
    return generateSHA256(inp.encode(), secret.encode())


def generateSHA256(message, secret):
    sign = hmac.new(secret, message, hashlib.sha256).hexdigest()
    # endpoint = "/authorization/202309/shops"
    # timestamp = int(time.time())
    # res = f"{DOMAIN}{endpoint}?app_key={APP_KEY}&sign={sign}&timestamp={timestamp}"
    # response = requests.get(res)
    # save_scratch_data(response.json(),"cipher")
    
    return sign


def get_access_token(sandbox=False):
    dynamic_name = frappe.get_value("Tiktok Credentials", filters={'idx': 0}, fieldname="name")
    
    # save_scratch_data(dynamic_name,'dynamic_name')
    if sandbox :
        # name = "01-12-24 TiktokCredentials 26333"
        credentials = frappe.get_doc("Tiktok Credentials", dynamic_name)
        domain = "https://auth-sandbox.tiktok-shops.com"

    else:
        # name = "Prod Token"
        credentials = frappe.get_doc("Tiktok Credentials", dynamic_name)
        domain = "https://auth.tiktok-shops.com"

    refresh_token = credentials.access_token
    return refresh_token


def is_json_key_present(json, key):
    try:
        buf = json[key]
    except KeyError:
        return False
    return True

@frappe.whitelist(allow_guest=True)
def clean_logs():
    count = 0
    doclist = frappe.db.get_all("Tiktok Webhook")
    for doc in doclist:
        frappe.db.delete("Tiktok Webhook", doc.name)
        
    frappe.db.commit()
    return dict(
        status_code=200,
        body="Clean logs success!",
        list_length=len(frappe.get_list("Tiktok Webhook")),
    )


# if __name__=='__main__':
#     main()
# cfa8480cdb0288ead599611f2e4fcaf95dfe3616/product/202309/products/1729743035114686731app_key6a8u5auuqugdushop_ciphernulltimestamp1697184279cfa8480cdb0288ead599611f2e4fcaf95dfe3616
