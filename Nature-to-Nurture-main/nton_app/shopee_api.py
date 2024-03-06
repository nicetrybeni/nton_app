import frappe
import pyshopee
import hmac
import json
import time
import requests
#from requests import *
import hashlib
from urllib.request import urlopen
from erpnext.stock.utils import get_stock_balance
from erpnext.accounts.doctype.payment_request.payment_request import (
    make_payment_request,
    make_payment_entry,
)
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
# from erpnext.stock.doctype.delivery_note.delivery_note import make_delivery_note
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note


from io import BytesIO
from datetime import datetime, timedelta

HOST_SB = "https://partner.test-stable.shopeemobile.com"
HOST = "https://partner.shopeemobile.com"
ORDER_PUSH = 3


# LIVE
@frappe.whitelist(allow_guest=True)
def shop_auth():
    timest = int(time.time())
    host = "https://partner.shopeemobile.com"
    path = "/api/v2/shop/auth_partner"
    redirect_url = "https://naturetonurture.rayasolutions.store/api/method/nton_app.shopee_api.auth_route"  ## Replace with redirect uri na sasalo ng data pag ka approve ng client
    partner_id = 2006532
    tmp = "70637a436d4947456552704d58575955525a4e6b73576e78746d4f74736b7551"
    partner_key = tmp.encode()
    tmp_base_string = "%s%s%s" % (partner_id, path, timest)
    base_string = tmp_base_string.encode()
    sign = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()
    ##generate api
    url = (
        host
        + path
        + "?partner_id=%s&timestamp=%s&sign=%s&redirect=%s"
        % (partner_id, timest, sign, redirect_url)
    )
    print(url)
    ## Next
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = url
    return url


@frappe.whitelist(allow_guest=True)
# first time request token
def auth_route(code, shop_id=None, main_account_id=None):
    package = {"code": code, "shop_id": shop_id, "main_account_id": main_account_id}

    save_scratch_data(package, "auth package")

    if main_account_id:
        return get_token_account_level(code, main_account_id)
    elif shop_id:
        return get_token_shop_level(code, shop_id)
    else:
        return None


@frappe.whitelist()
# first time request token
def get_token_shop_level(code, shop_id):
    timest = int(time.time())
    _, _, partner_id, _, partner_key = get_common_params(sandbox=False)
    host = "https://partner.shopeemobile.com"
    path = "/api/v2/auth/token/get"
    body = {"code": code, "shop_id": int(shop_id), "partner_id": partner_id}
    save_scratch_data(body, "body token")
    tmp_base_string = "%s%s%s" % (partner_id, path, timest)
    base_string = tmp_base_string.encode()
    sign = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()
    url = (
        host + path + "?partner_id=%s&timestamp=%s&sign=%s" % (partner_id, timest, sign)
    )
    # print(url)
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json=body, headers=headers)
    ret = json.loads(resp.content)
    save_scratch_data(ret, "prod token")
    access_token = ret.get("access_token")
    new_refresh_token = ret.get("refresh_token")

    doc = frappe.get_doc("Shopee Auth")
    doc.prod_access = access_token
    doc.prod_refresh = new_refresh_token
    doc.save()
    frappe.db.commit()
    return access_token, new_refresh_token


@frappe.whitelist(allow_guest=True)
def get_token_account_level(code, main_account_id):
    try:
        auth = frappe.form_dict
        save_scratch_data(str(auth), "auth query")
    except Exception as e:
        save_scratch_data(e, "auth query error")

    try:
        auth = json.loads(frappe.request.data)
        save_scratch_data(auth, "auth data")
    except:
        save_scratch_data(e, "auth data error")

    timest = int(time.time())
    _, _, partner_id, _, partner_key = get_common_params(sandbox=False)
    host = "https://partner.shopeemobile.com"
    path = "/api/v2/auth/token/get"
    body = {
        "code": code,
        "main_account_id": int(main_account_id),
        "partner_id": partner_id,
    }
    save_scratch_data(body, "body token")
    tmp_base_string = "%s%s%s" % (partner_id, path, timest)
    base_string = tmp_base_string.encode()
    sign = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()
    url = (
        host + path + "?partner_id=%s&timestamp=%s&sign=%s" % (partner_id, timest, sign)
    )
    # print(url)
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json=body, headers=headers)
    ret = json.loads(resp.content)
    save_scratch_data(ret, "prod token")
    access_token = ret["access_token"]
    new_refresh_token = ret["refresh_token"]

    doc = frappe.get_doc("Shopee Auth")
    doc.prod_access = access_token
    doc.prod_refresh = new_refresh_token
    doc.save()
    frappe.db.commit()
    return access_token, new_refresh_token


@frappe.whitelist()
# refresh token
def get_access_token_shop_level(shop_id, partner_id, tmp_partner_key, refresh_token):
    timest = int(time.time())
    host = "https://partner.test.shopeemobile.com"
    path = "/api/v2/auth/access_token/get"
    body = {
        "shop_id": shop_id,
        "refresh_token": refresh_token,
        "partner_id": partner_id,
    }
    tmp_base_string = "%s%s%s" % (partner_id, path, timest)
    base_string = tmp_base_string.encode()
    partner_key = tmp_partner_key
    sign = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()
    url = (
        host + path + "?partner_id=%s&timestamp=%s&sign=%s" % (partner_id, timest, sign)
    )
    # print(url)
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json=body, headers=headers)
    ret = json.loads(resp.content)
    access_token = ret.get("access_token")
    new_refresh_token = ret.get("refresh_token")
    return access_token, new_refresh_token


@frappe.whitelist()
def get_access_token_merchant_level(
    merchant_id, partner_id, tmp_partner_key, refresh_token
):
    timest = int(time.time())
    host = "https://partner.test.shopeemobile.com"
    path = "/api/v2/auth/access_token/get"
    body = {"merchant_id": merchant_id, "refresh_token": refresh_token}
    tmp_base_string = "%s%s%s" % (partner_id, path, timest)
    base_string = tmp_base_string.encode()
    partner_key = tmp_partner_key.encode()
    sign = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()
    url = (
        host + path + "?partner_id=%s&timestamp=%s&sign=%s" % (partner_id, timest, sign)
    )

    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json=body, headers=headers)
    ret = json.loads(resp.content)
    access_token = ret.get("access_token")
    new_refresh_token = ret.get("refresh_token")
    return access_token, new_refresh_token


# TEST
@frappe.whitelist(allow_guest=True)
def test_shop_auth():
    timest = int(time.time())
    host = "https://partner.test-stable.shopeemobile.com"
    path = "/api/v2/shop/auth_partner"
    redirect_url = "https://naturetonurture.rayasolutions.store/api/method/nton_app.shopee_api.test_get_token_shop_level"  ## Replace with redirect uri na sasalo ng data pag ka approve ng client
    partner_id = 1067444
    tmp = "515864624e49634164484c4470734b4c755375456f435a7479505a74624e6b6f"
    partner_key = tmp.encode()
    tmp_base_string = "%s%s%s" % (partner_id, path, timest)
    base_string = tmp_base_string.encode()
    sign = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()
    ##generate api
    url = (
        host
        + path
        + "?partner_id=%s&timestamp=%s&sign=%s&redirect=%s"
        % (partner_id, timest, sign, redirect_url)
    )
    print(url)
    ## Next
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = url
    return url


@frappe.whitelist(allow_guest=True)
def test_get_token_shop_level(code, shop_id):
    tmp_partner_key = "515864624e49634164484c4470734b4c755375456f435a7479505a74624e6b6f"
    partner_id = 1067444
    shop_id_conv = int(shop_id)
    timest = int(time.time())
    host = "https://partner.test-stable.shopeemobile.com"
    path = "/api/v2/auth/token/get"
    body = {"code": code, "shop_id": shop_id_conv, "partner_id": partner_id}
    tmp_base_string = "%s%s%s" % (partner_id, path, timest)
    base_string = tmp_base_string.encode()
    partner_key = tmp_partner_key.encode()
    sign = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()
    url = (
        host + path + "?partner_id=%s&timestamp=%s&sign=%s" % (partner_id, timest, sign)
    )
    print(url)
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json=body, headers=headers)
    ret = json.loads(resp.content)
    access_token = ret.get("access_token")
    new_refresh_token = ret.get("refresh_token")

    redirect_urlX = "https://naturetonurture.rayasolutions.store/api/method/nton_app.shopee_api.test_shopee_docs"
    bodyX = {
        "access_token": access_token,
        "new_refresh_token": new_refresh_token,
        "shop_id_conv": shop_id_conv,
    }
    urlX = redirect_urlX + "?access_token=%s&new_refresh_token=%s&shop_id_conv=%s" % (
        access_token,
        new_refresh_token,
        shop_id_conv,
    )
    print(urlX)
    headers = {"Content-Type": "application/json"}
    respX = requests.post(urlX, json=bodyX, headers=headers)
    retX = json.loads(respX.content)
    return retX


@frappe.whitelist(allow_guest=True)
def test_shopee_docs(access_token, new_refresh_token, shop_id_conv):
    doc = frappe.new_doc("Shopee Auth")
    doc.access_token = access_token
    doc.sales_type = "Shopee"
    doc.refresh_token = new_refresh_token
    doc.shop_id = shop_id_conv
    doc.insert(
        ignore_permissions=True,  # ignore write permissions during insert
    )

    return doc
    # Test


@frappe.whitelist(allow_guest=True)
def test_shopee_refresh():
    path = "/api/v2/auth/access_token/get"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params()
    refresh_token = frappe.get_doc("Shopee Auth").refresh_token
    params = {
        "timestamp": timestamp,
        "partner_id": partner_id,
    }
    payload = {
        "shop_id": shop_id,
        "refresh_token": refresh_token,
        "partner_id": partner_id,
    }
    temp_base_string = "%s%s%s" % (partner_id, path, timestamp)

    params["sign"] = get_sign(partner_key, temp_base_string)
    res = requests.post(url + path, params=params, json=payload)
    res = json.loads(res.content)
    save_scratch_data(res, "refresh token")

    doc = frappe.get_doc("Shopee Auth")
    doc.access_token = res["access_token"]
    doc.refresh_token = res["refresh_token"]
    doc.save()
    frappe.db.commit()
    return doc


@frappe.whitelist(allow_guest=True)
def shopee_refresh():
    path = "/api/v2/auth/access_token/get"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params(
        sandbox=False
    )
    refresh_token = frappe.get_doc("Shopee Auth").prod_refresh
    print("refresh_token:",refresh_token)
    params = {
        "timestamp": timestamp,
        "partner_id": partner_id,
    }
    payload = {
        "shop_id": shop_id,
        "refresh_token": refresh_token,
        "partner_id": partner_id,
    }
    save_scratch_data(payload, "refresh payload")
    temp_base_string = "%s%s%s" % (partner_id, path, timestamp)

    params["sign"] = get_sign(partner_key, temp_base_string)
    res = requests.post(HOST + path, params=params, json=payload)
    res = json.loads(res.content)
    save_scratch_data(res, "refresh token")
    print("Check 1")
    doc = frappe.get_doc("Shopee Auth")
    doc.prod_access = res["access_token"]
    doc.prod_refresh = res["refresh_token"]
    doc.save()
    frappe.db.commit()
    print("Check 1")
    return dict(
        status=200,
    )


@frappe.whitelist(allow_guest=True)
def test_shopee_push(data):
    # test
    # doc = frappe.new_doc("Testing REST")
    # doc.title = "Sample"
    # doc.content = str(data)
    return data


@frappe.whitelist(allow_guest=True)
def sync_shopee_product(product_id):
    path = "/api/v2/product/search_item"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params()
    item_name = product_id
    page_size = 10

    temp_base_string = "%s%s%s%s%s" % (
        partner_id,
        path,
        timestamp,
        access_token,
        shop_id,
    )

    base_string = temp_base_string.encode()

    sign = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()
    url = (
        HOST_SB
        + path
        + "?item_name=%s&page_size=%s&partner_id=%s&shop_id=%s&timestamp=%s&access_token=%s&sign=%s"
        % (item_name, page_size, partner_id, shop_id, timestamp, access_token, sign)
    )
    headers = {"Content-Type": "application/ison"}
    resp = requests.get(url, headers=headers)
    retX = json.loads(resp.content)
    save_scratch_data(retX)
    return retX


@frappe.whitelist(allow_guest=True)
def get_shop_info():
    path = "/api/v2/shop/get_shop_info"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params()
    temp_base_string = "%s%s%s%s%s" % (
        partner_id,
        path,
        timestamp,
        access_token,
        shop_id,
    )

    base_string = temp_base_string.encode()
    params = {}
    params["partner_id"] = partner_id
    params["timestamp"] = timestamp
    params["access_token"] = access_token
    params["shop_id"] = shop_id

    # save_scratch_data(partner_key,'pkey')
    params["sign"] = hmac.new(partner_key, base_string, hashlib.sha256).hexdigest()
    url = requests.get(HOST_SB + path, params=params).url
    headers = {"Content-Type": "application/json"}
    resp = requests.get(url, headers=headers)
    retX = json.loads(resp.content)
    save_scratch_data(retX, "shop_info")
    return retX


@frappe.whitelist(allow_guest=True)
def get_test_order():
    save_scratch_data("TESTING", "test")
    orders = get_order("240119AWDQTV9P", sandbox=True)
    print(orders)
    return insert_into_frappe(orders)
    # return get_order('231111BXV19DPW')


# TODO: remove whitelist; only added the whitelist for debugging
@frappe.whitelist(allow_guest=True)
def get_order(ordersn="240115VNF6D31A", sandbox=False):
    print("sandboooxxx---")
    print(sandbox)
    path = "/api/v2/order/get_order_detail"
    access_token, timestamp,  partner_id, shop_id, partner_key = get_common_params(
        sandbox=sandbox
    )
    print("--")
    print(access_token)
    print(shop_id)
    print(partner_id)
    print(partner_key)
    params = {
        "access_token": access_token,
        "order_sn_list": ordersn,
        "timestamp": timestamp,
        "request_order_status_pending":"true",
        "partner_id": partner_id,
        "shop_id": shop_id,
        "response_optional_fields": "buyer_user_id,buyer_username,estimated_shipping_fee,item_list,item_id,item_sku,parent_sku,package_list",
    }
    temp_base_string = "%s%s%s%s%s" % (
        partner_id,
        path,
        timestamp,
        access_token,
        shop_id,
    )
    print("-------:")
    print(params)
    print(temp_base_string)
    params["sign"] = get_sign(partner_key, temp_base_string)
    url = HOST_SB if sandbox else HOST
    res = requests.get(url + path, params=params, allow_redirects=False)

    #print(res['response'])
    #restest = requests.get(res.url,headers=headers, data=payload, allow_redirects=False)
    save_scratch_data(res.url, "order url")
    res = json.loads(res.text)
    save_scratch_data(res, "order details")
    print(res)
    return res['response']['order_list']


def insert_into_frappe(order_list):
    print("----------")
    print(order_list)
    sales_order = {"doctype": "Sales Order"}
    doc = ""
    item_frappe = []
    for order in order_list:
        try:
            sales_order["customer"] = frappe.get_doc("Customer", "Shopee Customer").name
            sales_order["company"] = "Nature to Nurture"
            sales_order["shopping_platform"] = "Shopee"
            sales_order["set_warehouse"] = frappe.get_doc(
                "Warehouse", "Store - Shopee - NTN"
            ).name
            sales_order["customer_name"] = order["buyer_user_id"]
            sales_order["transaction_date"] = unix_to_datetime(order["create_time"])
            try:
                sales_order["delivery_date"] = frappe.utils.add_days(
                    sales_order["transaction_date"], order["days_to_ship"]
                )
            except KeyError:
                sales_order["delivery_date"] = frappe.utils.add_days(
                    sales_order["transaction_date"], 3
                )
            sales_order["order_number"] = order["order_sn"]
            sales_order["selling_price_list"] = frappe.get_doc(
                "Price List", "Standard Selling"
            ).name

            for item_shopee in order["item_list"]:
                save_scratch_data(item_shopee, "item shopee")
                item_single = {"doctype": "Sales Order Item"}
                if item_shopee["model_sku"] != "":
                    item_single["item_code"] = item_shopee["model_sku"]
                else:
                    item_single["item_code"] = item_shopee["item_sku"]
                item_single["qty"] = item_shopee["model_quantity_purchased"]
                # item_single['rate'] = item_shopee['model_original_price']
                item_single["price_list_rate"] = item_shopee["model_original_price"]
                item_single["discount_percentage"] = 100.0 - (
                    item_shopee["model_discounted_price"]
                    * 100.0
                    / item_shopee["model_original_price"]
                )
                item_frappe.append(item_single)

            save_scratch_data(item_frappe, "frappe items")

            sales_order["items"] = item_frappe
            doc = frappe.get_doc(sales_order)
            doc.insert(ignore_permissions=True)
            # save_scratch_data(doc,'sales order')
            # for idx, item in enumerate(doc.items):
            #     item.discount_amount = order['item_list'][idx]['model_original_price'] - order['item_list'][idx]['model_discounted_price']
            #     item.discount_percentage = 5
            # doc.save()
            frappe.db.commit()
        except Exception as e:  # originally KeyError
            return {
                "status": 200,
                "message": "got error with message: " + str(e)
            }

    return {"status": 200}


@frappe.whitelist(allow_guest=True)
def shopee_sb_webhook():
   
    req = ""
    if frappe.request.data != b"":
        req = json.loads(frappe.request.data)
    else:
        return {"status code": 200}
    #frappe.publish_realtime('event_name', data={'msg': str(req)})
    save_scratch_data(req, "webhook")
    shopee_webhook(req, sandbox=True)
    return {"status code": 200}


@frappe.whitelist(allow_guest=True)
def shopee_prod_webhook():
    req = ""
    if frappe.request.data != b"":
        req = json.loads(frappe.request.data)
    else:
        return {"status": 200}
    save_scratch_data(req, "webhook")
    shopee_webhook(req, sandbox=False)
    return {"status": 200}


@frappe.whitelist(allow_guest=True)
def shopee_webhook(req, sandbox=False):
    # in case req is string, parse to object
    if(type(req) is str):
        req = json.loads(req)
    
    sandbox = sandbox == True
    try:
        if req["code"] == ORDER_PUSH:
            status = req["data"]["status"]
            if status == "UNPAID":
                pass
            elif status == "READY_TO_SHIP":
                orders = get_order(req["data"]["ordersn"], sandbox=sandbox)
                return insert_into_frappe(orders)
            elif status == "PROCESSED":
                # update the existing sales order's allowed delivery dates
                # return update_sales_order_processed(req["data"]["ordersn"], sandbox=sandbox)
                return ship_order_new(req["data"]["ordersn"], sandbox=sandbox)
            elif status == "SHIPPED":
                pass
            elif status == "RETRY_SHIP":
                pass
            elif status == "TO_CONFIRM_RECEIVE":
                pass
            elif status == "IN_CANCEL":
                pass
            elif status == "CANCELLED":
                pass
            elif status == "TO_RETURN":
                pass
            elif status == "COMPLETED":
                pass
        return {"status": 200}
    except Exception as e:
        save_scratch_data(e, "webhook error")
        return {
            "status": 200,
            "message": "caught exception: " + str(e)
        }


def update_sales_order_processed(order_id, sandbox=False):
    fetched_so = frappe.db.sql(
        f"""SELECT name,customer,order_number FROM `tabSales Order` WHERE order='{order_id}' AND shopping_platform='Shopee';""",
        as_dict=True,
    )
    if not fetched_so:  # no existing SO yet; return an error
        return dict(
            status_code=400,
            msg="No existing sales order to mark it as processed!"
        )
    
    fetched_so = fetched_so[0]

    # TODO: update the fields below. Fetch the dates from the get_shipping_parameter API
    fetched_so.update({
        "delivery_date_allowed": "[01/29/2024,01/30/2024]"
    })
    fetched_so.save()


@frappe.whitelist(allow_guest=True)
def ship_order_new(order_id, sandbox=False):
    url = "https://naturetonurture.rayasolutions.store/api/method/"
    path = "nton_app.shopee_api.ship_order_new_helper"
    headers = {
        "Authorization": "Token e2624ee0eba9640:38ecfa3de786d24",
        "Content-Type": "application/json"
    }
    payload = {
        "order_id": order_id
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
            message="error - pushmech order_status packed (No Sales Order found!)"
        )
    
    # submit the sales order and create the delivery note
    try:
        existing_so_fetched = frappe.get_doc("Sales Order", existing_so[0].name)
        existing_so_fetched_dict = existing_so_fetched.as_dict()
        existing_so_fetched.save(ignore_permissions=True)
        if existing_so_fetched_dict["docstatus"]==0:
            existing_so_fetched.submit()
        
        if existing_so_fetched_dict["delivery_status"]!="Not Delivered": # ! assume that the delivery notes are submitted for the whole order (not per item)
            raise Exception("The current sales order already has a bound delivery note!")
        
        
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
        

        """
        # ! manually create the delivery note from the Sales Order
        # Create a new Delivery Note
        delivery_note = frappe.new_doc('Delivery Note')
        delivery_note.customer = existing_so_fetched.customer
        delivery_note.company = existing_so_fetched.company
        delivery_note.delivery_date = frappe.utils.nowdate()  # Or another appropriate date
        delivery_note.sales_order = existing_so[0].name  # Link to the Sales Order

        # Copy items from Sales Order to Delivery Note
        for item in existing_so_fetched_dict["items"]:
            dn_item = delivery_note.append('items', {})
            dn_item.item_code = item.item_code
            dn_item.item_name = item.item_name
            dn_item.qty = item.qty
            dn_item.stock_uom = item.stock_uom
            dn_item.description = item.description
            dn_item.warehouse = item.warehouse
            # Copy other necessary fields as needed

        # Save and submit the Delivery Note
        delivery_note.flags.ignore_permissions = True  # Use with caution!
        delivery_note.insert()
        delivery_note.save()
        delivery_note.submit()
        """

    except Exception as e:
        save_scratch_data(str(e),"error (TRY/EXCEPT block) - pushmech order_status packed")
        return dict(
            status=400,
            message=f"error (TRY/EXCEPT block) - {str(e)}"
        )
    else:
        # Ensure that permission checks are restored to their original state
        return dict(
            status=200,
        )


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


def get_shipping_parameter(order_id, sandbox=False):
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
    save_scratch_data(res, "shipping params")
    return res["response"]


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
def get_waybill(order_id="24020823VH54XF", sandbox=False):
    frappe.msgprint(order_id)
    sandbox = sandbox == True
    package_number = get_order(order_id).pop(0)["package_list"].pop(0)["package_number"]
    ship_params = {"package_number": package_number}
    print("ship_params:")
    print(ship_params)

    tracking_num = get_tracking_number(order_id, ship_params, sandbox=sandbox)
    # if tracking_num == '':
    #     save_scratch_data('no tracking num', 'no tracking num')
    #     return {'message' : 'Waybill not yet ready'}
    print("tracking_num:",tracking_num)

    document_params = get_shipping_document_parameters(
        order_id, ship_params, sandbox=sandbox
    )
    selected_document_type = document_params[0]["suggest_shipping_document_type"]
    
    print("document_params:",document_params)
    shipping_document = create_shipping_document(
        order_id, tracking_num, ship_params, selected_document_type=selected_document_type, sandbox=sandbox
    )

    print("shipping_document:",shipping_document)
    rdy = get_shipping_document_result(order_id, ship_params, sandbox=sandbox)
    print("rdy:",str(rdy))
    
    try:
        if rdy["response"]["result_list"].pop(0)["status"] != "READY":
            return {"status_code": 400, "message": "Waybill not yet ready"}
    except KeyError:
        pass
    res = download_shipping_document(order_id, ship_params, selected_document_type, sandbox=sandbox)
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
                "package_number": shipping_params["package_number"],
            }
        ],
    }
    params["sign"] = get_sign(partner_key, temp_base_string)
    url = HOST_SB if sandbox else HOST
    res = requests.post(url + path, params=params, json=payload)
    res = json.loads(res.content)
    
    save_scratch_data(res, "shipping document params")
    return res["response"]["result_list"]


def create_shipping_document(order_id, tracking_num, shipping_params, selected_document_type, sandbox=True):
    # frappe.msgprint(shipping_params)
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
                'shipping_document_type' : selected_document_type,
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


def download_shipping_document(order_id, shipping_params, selected_document_type, sandbox=True):
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
        "shipping_document_type": selected_document_type,
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
def upload_img(sandbox=False):
    path = "/api/v2/media_space/upload_image"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params(
        sandbox=sandbox
    )
    params = {
        "timestamp": timestamp,
        "partner_id": partner_id,
    }
    temp_base_string = "%s%s%s" % (partner_id, path, timestamp)

    params["sign"] = get_sign(partner_key, temp_base_string)
    image_url = "https://naturetonurture.rayasolutions.store/files/placeholder.png"
    image = urlopen(image_url).read()
    # save_scratch_data(image,'image')
    files = [("image", ("image", image, "application/octet-stream"))]
    url = HOST_SB if sandbox else HOST
    res = requests.post(url + path, params=params, files=files)
    res = json.loads(res.content)
    save_scratch_data(res, "upload img")
    return res


@frappe.whitelist(allow_guest=True)
def get_eligible_categories(sandbox=False):
    path = "/api/v2/product/get_category"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params(
        sandbox=sandbox
    )
    # originally sandbox=True
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
    print("test--------------")
    print(sandbox)
    print(access_token)
    print(shop_id)
    print(partner_id)
    params["sign"] = get_sign(partner_key, temp_base_string)
    url = HOST_SB if sandbox else HOST
    res = requests.get(url + path, params=params)
    res = json.loads(res.content)
    #frappe.msgprint(str(res['response']))
    save_scratch_data(res, "categories 0")
    category_list = res['response']["category_list"]
    leaf_categories = []
    for category in category_list:
        if category["has_children"] == False:
            leaf_categories.append(category)
    save_scratch_data(leaf_categories, 'categories')
    return leaf_categories

# api for warehouse / added by clifford
@frappe.whitelist(allow_guest=True)
def get_merchant_warehouse(sandbox=False):
    path = "/api/v2/shop/get_warehouse_detail"
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

    url = HOST_SB if sandbox else HOST
    res = requests.get(url + path, params=params)
    res = json.loads(res.content)
    save_scratch_data(res, "warehouse list")

#########

@frappe.whitelist(allow_guest=True)
def get_attributes(category_id):
    path = "/api/v2/product/get_attributes"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params()
    params = {
        "access_token": access_token,
        "timestamp": timestamp,
        "partner_id": partner_id,
        "shop_id": shop_id,
        "category_id": category_id,
    }
    temp_base_string = "%s%s%s%s%s" % (
        partner_id,
        path,
        timestamp,
        access_token,
        shop_id,
    )

    params["sign"] = get_sign(partner_key, temp_base_string)
    res = requests.get(HOST_SB + path, params=params)
    res = json.loads(res.content)

    save_scratch_data(res, " attributes")
    attribute_list = res["response"]["attribute_list"]

    mandatory = []
    for attribute in attribute_list:
        if attribute["is_mandatory"] == True:
            mandatory.append(attribute)
    # save_scratch_data(mandatory, 'mandatory')
    return mandatory


@frappe.whitelist(allow_guest=True)
def get_logistics_channels(sandbox=False):
    path = "/api/v2/logistics/get_channel_list"
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
    url = HOST_SB if sandbox else HOST
    res = requests.get(url + path, params=params)
    res = json.loads(res.content)

    save_scratch_data(res, " logistics")
    #res = res["response"]["logistics_channel_list"]
    frappe.msgprint(str(res))
    # save_scratch_data(mandatory, 'mandatory')
    return res


@frappe.whitelist(allow_guest=True)
def get_brand_list(category_id):
    path = "/api/v2/product/get_brand_list"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params()
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
    params["offset"] = 0
    params["page_size"] = 50
    params["category_id"] = category_id
    params["status"] = 1
    res = requests.get(HOST_SB + path, params=params)
    res = json.loads(res.content)

    res = res["response"]
    save_scratch_data(res, "brands")

    # save_scratch_data(mandatory, 'mandatory')
    return res



@frappe.whitelist(allow_guest=True)
def test_fetch_product_list(sandbox=False):
    path = "/api/v2/product/get_item_list"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params()
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
    params["offset"] = 0
    params["page_size"] = 100
    params["item_status"] = ["NORMAL"]

    url = HOST_SB if sandbox else HOST
    res = requests.get(url + path, params=params)
    res = json.loads(res.content)

    save_scratch_data(res, "fetched products")
    res = res["response"]

    # save_scratch_data(mandatory, 'mandatory')
    return res

@frappe.whitelist(allow_guest=True)
def test_fetch_product(item_id=966711921, sandbox=False):
    path = "/api/v2/product/get_item_base_info"
    access_token, timestamp, partner_id, shop_id, partner_key = get_common_params()
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
    params["item_id_list"] = [item_id]

    url = HOST_SB if sandbox else HOST
    res = requests.get(url + path, params=params)
    res = json.loads(res.content)

    save_scratch_data(res, "single fetched product")
    res = res["response"]

    # save_scratch_data(mandatory, 'mandatory')
    return res

@frappe.whitelist(allow_guest=True)
def insert_product(item, sandbox=False):
    # 01/11/2024: modified froms sandbox=True to sandbox=False
    item = json.loads(item)
    sandbox = sandbox == True
    # attributes = []
    # attribute_details = get_attributes(item['category_id'])
    # attribute_name_to_id = {} # mapping of attrib name : attrib id
    # attribute_value_name_to_id = {}
    # for attribute in attribute_details:
    #     attrib_name = attribute['attribute_name']
    #     attrib_id = attribute['attribute_id']
    #     attribute_name_to_id[attrib_name] = attrib_id

    #     attribute_value_name_to_id[attrib_name] = dict(zip(attribute['values_name'], attribute['values_id']))
    #     # use case: attribute_value_name_to_id[attribute_name] -> get mapping of value to id PER attribute
    #     #           attribute_value_name_to_id[attribute_name][attribute_value] -> id of attribute value

    # get id of attrib
    # get id of value
    # attribute { attrib_id , value_id }
    # save_scratch_data(item, 'item')
    # for attribute in item['item_attributes']:
    #     builder = {}
    #     builder['attribute_id'] = attribute_name_to_id[attribute['attrib_name']]

    #     if(attribute['attrib_value'] == 'Enter custom value'):
    #         builder['custom_value'] = 'Custom'
    #     else:
    #         builder['value_id'] = attribute_value_name_to_id[attribute['attrib_name']][attribute['attrib_value']]

    #     attributes.append(builder)
    # save_scratch_data(attributes, 'item_attributes')

    it = frappe.get_doc("Item", item["item_code"]).name
    wh = frappe.get_doc("Warehouse", "Store - Shopee - NTN").name
    stock = get_stock_balance(it, wh)
    save_scratch_data(stock, "stock1")

    item["stock"] = int(stock)
    # sku = [{
    #     'seller_sku' : item['item_code'],
    #     'original_price' : str(item['valuation_rate']),
    #     'stock_infos' : [{
    #         'warehouse_id' : item['warehouse_id'],
    #         'available_stock' : int(stock)
    #     }],
    # #     'sales_attributes' : s_attributes,
    # }]
    seller_stock = [{"stock": item["stock"]}]

    image = upload_img(sandbox=sandbox)
    images = {"image_id_list": [image["response"]["image_info"]["image_id"]]}

    logistic_channels = get_logistics_channels(sandbox=sandbox)
    frappe.msgprint(str(logistic_channels))
    logistic_info = []
    for channel in logistic_channels['response']['logistics_channel_list']:
        logistic_info.append(
            {
                "logistic_id": channel["logistics_channel_id"],
                "enabled": channel["enabled"],
                "size_id": 1,
                "shipping_fee": 0,
            }
        )

    brand = {"brand_id": 0}
    body = {
        "item_name": item["item_name"],
        "category_id": item["category_id"],
        "image": images,
        "logistic_info": logistic_info,
        "brand": brand,
        "package_height": 10,
        "package_length": 10,
        "package_weight": 10,
        "package_width": 10,
        "product_name": item["item_name"],
        "original_price": item["shopee_selling_price"],
        "seller_stock": seller_stock,
        "item_status": "NORMAL",
        "weight": 5.0,
        "description_type": "normal",
        "description": item["description"],
        "item_sku": item["item_code"],
        "item_id":item["item_code"]
    }
    save_scratch_data(item, "item info")
    path = "/api/v2/product/add_item"
    if is_json_key_present(item, "item_id"):
        if item["item_id"] != "":
            body["product_id"] = item["item_id"]
        else:
            body["product_id"] = None
    else:
        body["product_id"] = None
        path = "/api/v2/product/add_item"
    save_scratch_data(body, "product info")

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
    url = HOST_SB if sandbox else HOST
    res = ""
    if body["product_id"] is None:  # draft
        try:
            res = requests.post(url + path, params=params, json=body)
            res = json.loads(res.content)
            save_scratch_data(body, "item info")
            save_scratch_data(res, "insert resp")
        except Exception as e:
            save_scratch_data(e, "error d")
        return res
    else:  # update stock and price
        try:
            # res = requests.put(DOMAIN+path, params=params, json=body)
            res_s = update_stock(item, sandbox=sandbox)
            res_p = update_price(item, sandbox=sandbox)
            res = str(res_p) + str(res_s)
            save_scratch_data(res, "upd product")
        except Exception as e:
            save_scratch_data(e, "error u")
        
        return dict(
            need_to_update=False
        )

    return res


@frappe.whitelist(allow_guest=True)
def test_upd_stock():
    item = {"item_id": 21388586080, "stock": 345}
    return update_stock(item, sandbox=False)


def update_stock(item, sandbox=False):
    path = "/api/v2/product/update_stock"
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
    body = {
        "item_id": int(item["item_id"]),
        "stock_list": [
            {
                "model_id": 0,
                "seller_stock": [
                    {
                        "stock": int(item["stock"]),
                    }
                ],
            },
        ],
    }
    body = json.dumps(body)

    headers = {"Content-Type": "application/json"}
    url = HOST_SB if sandbox else HOST
    res = requests.post(url + path, params=params, data=body, headers=headers)
    res = json.loads(res.content)

    save_scratch_data(res, "update stock")
    return res


@frappe.whitelist(allow_guest=True)
def test_upd_price():
    item = {"item_id": 21388586080, "valuation_rate": 99997}
    return update_price(item, sandbox=False)


def update_price(item, sandbox=False):
    path = "/api/v2/product/update_price"
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
    body = json.dumps(
        {
            "item_id": int(item["item_id"]),
            "price_list": [
                {"model_id": 0, "original_price": int(item["shopee_selling_price"])},
            ],
        }
    )
    save_scratch_data(body, "upd price item2")
    headers = {"Content-Type": "application/json"}
    url = HOST_SB if sandbox else HOST
    res = requests.post(url + path, params=params, data=body, headers=headers)
    res = json.loads(res.content)

    save_scratch_data(res, "update price")
    return res


@frappe.whitelist()
def get_escrow(order_id="2401175FNXAURR", sandbox=False):   # temporary order_sn
    sandbox = sandbox == True
    if sandbox:
        save_scratch_data(sandbox, "escrow")
        return {"response": {"escrow_amount_after_adjustment": 1950}}
    else:
        save_scratch_data("not sb", "escrow")
        path = "/api/v2/payment/get_escrow_detail"
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
        body = {
            "order_sn": order_id,
        }
        url = (HOST_SB if sandbox else HOST) + path
        res = requests.post(url, params=params, json=body)
        res = json.loads(res.content)

        save_scratch_data(res, "escrow details")
        return res


@frappe.whitelist(allow_guest=True)
def test_remittance():
    return get_single_remittance(False)


def get_single_remittance(sandbox=True):
    sql = """SELECT name,customer,order_number,total FROM `tabDelivery Note` WHERE status='To Bill' AND shopping_platform='Shopee' AND order_number='231113GKR5R1CU';"""
    dn_billable = frappe.db.sql(sql, as_dict=True)
    save_scratch_data(dn_billable, "single dn billable")
    for dn_single in dn_billable:
        try:
            new_si = make_sales_invoice(dn_single["name"])
            response_order_json = get_escrow(dn_single["order_number"], sandbox=sandbox)
            new_si.insert()
            new_si_fetched = frappe.get_last_doc("Sales Invoice")
            sales_and_tax_single = frappe.new_doc("Sales Taxes and Charges")
            sales_and_tax_single.update(
                {
                    "charge_type": "Actual",
                    "account_head": "Miscellaneous Expenses - NTN",
                    "description": "Miscellaneous Expenses",
                    "cost_center": "Main - NTN",
                    "account_currency": "PHP",
                    "tax_amount": float(dn_single.total)
                    - float(
                        response_order_json["response"]["order_income"][
                            "escrow_amount_after_adjustment"
                        ]
                    ),
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
        except KeyError as e:
            save_scratch_data(e, "remittance err")
            continue
    frappe.db.commit()

# ! old version; use new version of get_remittances below instead!
@frappe.whitelist(allow_guest=True)
def get_remittances_old(sandbox=False):
    dn_billable = frappe.db.sql(
        """SELECT name,customer,order_number,total FROM `tabDelivery Note` WHERE status='To Bill' AND shopping_platform='Shopee';""",
        as_dict=True,
    )
    save_scratch_data(dn_billable, "dn billable")
    for dn_single in dn_billable:
        try:
            new_si = make_sales_invoice(dn_single["name"])
            response_order_json = get_escrow(dn_single["order_number"], sandbox)
            new_si.insert()
            new_si_fetched = frappe.get_last_doc("Sales Invoice")
            sales_and_tax_single = frappe.new_doc("Sales Taxes and Charges")
            sales_and_tax_single.update(
                {
                    "charge_type": "Actual",
                    "account_head": "Miscellaneous Expenses - NTN",
                    "description": "Miscellaneous Expenses",
                    "cost_center": "Main - NTN",
                    "account_currency": "PHP",
                    "tax_amount": float(dn_single.total)
                    - float(
                        response_order_json["response"]["order_income"][
                            "escrow_amount_after_adjustment"
                        ]
                    ),
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

# ! NEW: getting list of PAID orders
@frappe.whitelist(allow_guest=True)
def get_remittances(sandbox=False): # revised remittances function
    # fetch all pending delivery notes
    dn_billable = frappe.db.sql(
        """SELECT name,customer,order_number,total FROM `tabDelivery Note` WHERE status='To Bill' AND shopping_platform='Shopee';""",
        as_dict=True,
    )
    save_scratch_data(dn_billable, "dn billable")
    
    # fetching the transaction list
    # // save_scratch_data("not sb", "escrow")
    path = "/api/v2/payment/get_wallet_transaction_list"
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
    params["page_no"] = 1
    params["page_size"] = 20
    params["create_time_from"] = int((datetime.now() - timedelta(days=1)).timestamp())
    params["create_time_to"] = int((datetime.now()).timestamp())
    params["transaction_type"] = "ESCROW_VERIFIED_ADD"
    
    url = (HOST_SB if sandbox else HOST) + path
    page_no_ctr = 1
    more_items = True
    transac_list = {}   # contains all transactions in key->value format: order_sn: amount
    
    while more_items is True:
        params["page_no"] = page_no_ctr
        res = requests.get(url, params=params)
        res = json.loads(res.content)
        save_scratch_data(res, ("escrow details " + str(page_no_ctr)))
        
        for a_transac in res["response"]["transaction_list"]:
            transac_list[a_transac["order_sn"]] = a_transac["amount"]
        
        # print("Current Number of transactions:",len(transac_list.keys()))
        # increment page
        page_no_ctr += 1
        more_items = res["response"]["more"]
        
    # ? res structure
    # ??? "more" -- checks if there are more entries after the current page
    # ??? "transaction_list" -- contains the list of transactions; fetch the order_sn and amount!
    
    # print("Final Number of transactions:",len(transac_list.keys()))
    # print("end of transmittal fn")
    save_scratch_data(transac_list, ("completed transactions w/in 1 day"))
    finished_order_sn = transac_list.keys()
    
    # ! create sales invoice for each delivery note found in the list
    for dn_single in dn_billable:
        if dn_single["order_number"] in finished_order_sn:
            print("Order number",dn_single["order_number"],"for billing...")
            try:
                new_si = make_sales_invoice(dn_single["name"])
                response_order_json = get_escrow(dn_single["order_number"], sandbox)
                new_si.insert()
                new_si_fetched = frappe.get_last_doc("Sales Invoice")
                sales_and_tax_single = frappe.new_doc("Sales Taxes and Charges")
                sales_and_tax_single.update(
                    {
                        "charge_type": "Actual",
                        "account_head": "Miscellaneous Expenses - NTN",
                        "description": "Miscellaneous Expenses",
                        "cost_center": "Main - NTN",
                        "account_currency": "PHP",
                        "tax_amount": float(dn_single.total)
                        - float(
                            response_order_json["response"]["order_income"][
                                "escrow_amount_after_adjustment"
                            ]
                        ),
                        "parenttype": "Sales Invoice",
                        "parent": new_si_fetched.name,
                        "parentfield": "taxes",
                        "idx": 0,
                    }
                )

                sales_and_tax_single.save()
                # new_si.taxes.append(sales_and_tax_single)
                new_si.save()
                new_si.submit()

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
            except KeyError as e:
                save_scratch_data(str(e), "Error in creating sales invoice/remittance")
                continue
    
    return dict(
        status=200
    )


@frappe.whitelist(allow_guest=True)
def cron_update_stocks(sandbox=False):
    sp_items = frappe.db.sql(
        """SELECT name, sp_item_id FROM `tabItem` WHERE sp_item_id > '';""",
        as_dict=True,
    )
    wh = frappe.get_doc("Warehouse", "Store - Shopee - NTN").name
    save_scratch_data(sp_items, "cron shopee update")
    for item_single in sp_items:
        try:
            stock = get_stock_balance(item_single["name"], wh)
            item_details = {
                "item_id": int(item_single["sp_item_id"]),
                "stock": int(stock),
            }
            update_stock(item_details, sandbox=sandbox)
        except KeyError:
            continue

@frappe.whitelist(allow_guest=True)
def clean_logs():
    count = 0
    doclist = frappe.db.get_all("Shopee Logs")
    for doc in doclist:
        frappe.db.delete("Shopee Logs", doc.name)
        
    frappe.db.commit()
    return dict(
        status_code=200,
        body="Clean logs success!",
        list_length=len(frappe.get_list("Shopee Logs")),
    )

def save_scratch_data(data, tags):
    doc = frappe.get_doc(
        {"doctype": "Shopee Logs", "content": str(data), "tags": str(tags)}
    )
    doc.insert()
    frappe.db.commit()


def get_common_params(sandbox=False):
    auth = frappe.get_doc("Shopee Auth")
    access_token = auth.access_token if sandbox else auth.prod_access
    print("-----getting common params---")
    # print(auth.access_token)
    # print(access_token)
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
    # print("access_token here")
    # print(access_token)
    # print(shop_id)
    # print(partner_id)
    # print(partner_key)

    #return ('544b737546656e65654948646b42434b', timestamp, '1067444', '93614',sb_partner)
    return (access_token, timestamp, partner_id, shop_id, partner_key)

def get_sign(partner_key, base_string):
    return hmac.new(partner_key, base_string.encode(), hashlib.sha256).hexdigest()


def unix_to_datetime(unix):
    unix = int(unix) // 1  # shopee in seconds
    NUM_OF_SEC_IN_DAYS = 86400
    return frappe.utils.add_days(
        frappe.utils.get_datetime("1970-01-01"), (unix) / NUM_OF_SEC_IN_DAYS
    )


def is_json_key_present(json, key):
    try:
        buf = json[key]
    except KeyError:
        return False
    return True
