import frappe
import hmac
import json
import time
import requests
import hashlib
import shopify
import binascii
import os
from datetime import datetime, date, timedelta
from lazop_sdk import LazopClient, LazopRequest
from erpnext import get_default_company
from erpnext.stock.utils import get_stock_balance
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note


SUCCESS = 200
NOT_FOUND = 400

### Lazada API Variables
# url = "https://api.lazada.com.my/rest"
url = "https://api.lazada.com.ph/rest"
appkey = 126275
appSecret = "7IrbxBBHReeC3DaApuBX13dFtu4BZtjT"
access_token = "50000001020q32taaYK2goph0Sc6ibv91d89e18eos2dfEtJvltzjl5jsoHi4ZVp"

so_company = None   # default company
########################


@frappe.whitelist(allow_guest=True)
def get_all_items():
    # items = frappe.db.sql("""SELECT name,customer,order_number FROM `tabSales Order` WHERE status='To Bill' AND shopping_platform='Lazada';""", as_dict=True)
    # items = frappe.db.sql("""SELECT * FROM `tabSales Invoice`;""", as_dict=True)
    """
    si = frappe.get_doc({
        "doctype": "Sales Invoice",
        "quickbooks_invoce_id" : qb_orders.get("Id"),
        "naming_series": "SI-Quickbooks-",
        "customer": frappe.db.get_value("Customer",{"quickbooks_cust_id":qb_orders['CustomerRef'].get('value')},"name"),
        "posting_date": qb_orders.get('TxnDate'),
        "territory" : frappe.db.get_value("Customer",{"quickbooks_cust_id":qb_orders['CustomerRef'].get('value')},"territory"),
        "selling_price_list": quickbooks_settings.selling_price_list,
        "ignore_pricing_rule": 1,
        "apply_discount_on": "Net Total",
        "items": get_order_items(qb_orders['Line'], quickbooks_settings),
        "taxes": get_order_taxes(qb_orders)
    })
    """

    items = frappe.db.sql(
        """SELECT name,customer,shopping_platform FROM `tabSales Order` WHERE order_number='399667396843475';""",
        as_dict=True,
    )
    return items
    # return items[0]


@frappe.whitelist(allow_guest=True)
def laz_test():
    resp = requests.get(
        "https://api.lazada.com.ph/rest/orders/get?sort_direction=DESC&offset=0&created_after=1999-10-10T16%3A00%3A00%2B08%3A00&limit=30&sort_by=updated_at&status=ready_to_ship&app_key=126275&sign_method=sha256&access_token=50000600621qhqtLfuBiCwVuR9b2otcpQ18526e15h0rCYEjrgkTuefILEHM1Ppg&timestamp=1695839744760&sign=7AD8CEC1F07333937DB359F536DD745F49657B658AFFFC0F9487E5F28B34A9B8"
    )
    ret = json.loads(resp.content)
    all_orders = ret["data"]["orders"]
    print("Number of orders ready:", ret["data"]["countTotal"])
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

    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Order List Update",
            "count": ret["data"]["countTotal"],
            "order": list_of_orders,
        }
    )

    add_item.insert(ignore_permissions=True)
    frappe.db.commit()

    return add_item


@frappe.whitelist(allow_guest=True)
def test_url_with_params(param1, param2):
    # after running the seller auth, this will redirect to this function (Frappe URL) through a POST request
    # the body contains the following: code (String), shop_id (int), main_account_id (int; only if main account was used to log in)
    return dict(status_code=200, param1=param1, param2=param2)


@frappe.whitelist(allow_guest=True)
def lazada_product_push(item_obj):
    fetch_latest_access_code()
    item_obj_json = json.loads(item_obj)

    # ! It is assumed that the Item Code is a VALID SKU
    ### "SellerSku": item_obj_json["seller_sku"]
    # ! Note Malaysia PrimaryCategory: "10001100"
    # ! PH Category (Sleeping Bags): "7665"
    ### also commented for PH --> "brand": "No Brand", instead of "Nature to Nurture"
    
    # temp_primary_category = "7665"
    # temp_brand = "Nature to Nurture"
    temp_primary_category = "10001100"
    temp_brand = "No Brand"

    # ! Check if product exists. Else, update the price/product info only (needs 2 APIs)

    if(("laz_item_id" not in item_obj_json.keys()) or ("laz_sku_id" not in item_obj_json.keys()) or (item_obj_json["laz_item_id"] in [None,""]) or (item_obj_json["laz_sku_id"] in [None,""])): # means product was never pushed. Insert the product...
        new_product = {
            "Request": {
                "Product": {
                    "PrimaryCategory": temp_primary_category,
                    "Images": {
                        "Image": [
                            "https://my-live-02.slatic.net/p/47b6cb07bd8f80aa3cc34b180b902f3e.jpg"
                        ]
                    },
                    "Attributes": {
                        "name": item_obj_json["item_name"],
                        "description": ("Description with " + item_obj_json["item_code"]),
                        "brand": temp_brand,
                        "model": "test",
                        "waterproof": "Waterproof",
                        "warranty_type": "Local Supplier Warranty",
                        "warranty": "1 Month",
                        "short_description": "cm x 1efgtecm<br /><brfwefgtek",
                        "Hazmat": "None",
                        "material": "Leather",
                        "laptop_size": "11 - 12 inches",
                        "delivery_option_sof": "No",
                        "name_engravement": "Yes",
                        "gift_wrapping": "Yes",
                        "preorder_enable": "No",
                        "preorder_days": "25",
                    },
                    "Skus": {
                        "Sku": [
                            {
                                "SellerSku": item_obj_json["item_code"],
                                "quantity": "0",
                                "price": item_obj_json["price"],
                                "package_height": item_obj_json["item_height"],
                                "package_length": item_obj_json["item_length"],
                                "package_width": item_obj_json["item_width"],
                                "package_weight": item_obj_json["item_weight"],
                                "package_content": "laptop bag",
                                "Images": {
                                    "Image": [
                                        "https://my-live-02.slatic.net/p/47b6cb07bd8f80aa3cc34b180b902f3e.jpg"
                                    ]
                                },
                            }
                        ]
                    },
                }
            }
        }

        # image original sample: https://my-live-02.slatic.net/p/47b6cb07bd8f80aa3cc34b180b902f3e.jpg

        client = LazopClient(url, appkey, appSecret)
        request = LazopRequest("/product/create")
        request.add_api_param("payload", json.dumps(new_product))
        response = client.execute(request, access_token)

        prod_response_json = response.body

        add_item = frappe.get_doc(
            {
                "doctype": "Lazada Push Mechanism Logs V2",
                "push_type": "Product Push error",
                "push_msg": json.dumps(prod_response_json) + access_token,
            }
        )
        add_item.insert(ignore_permissions=True)
        frappe.db.commit()

        # deactivate the product
        product_id_to_deactivate = prod_response_json["data"]["item_id"]
        product_to_deactivate = f"""
            <Request>
                <Product>
                    <ItemId>{product_id_to_deactivate}</ItemId>
                </Product>
            </Request>    
        """

        request = LazopRequest("/product/deactivate")
        request.add_api_param("apiRequestBody", product_to_deactivate)
        response2 = client.execute(request, access_token)

        # add the SKU ID and Item ID
        try:
            item_new_push = frappe.get_doc("Item", item_obj_json["item_code"])
            item_new_push.update(
                {
                    "laz_item_id": product_id_to_deactivate,
                    "laz_sku_id": prod_response_json["data"]["sku_list"][0]["sku_id"],
                }
            )
            # item_new_push["laz_item_id"] = product_id_to_deactivate
            # item_new_push["laz_sku_id"] = prod_response_json["data"]["sku_list"][0]["sku_id"]
            item_new_push.save()
        except:
            add_item = frappe.get_doc(
                {
                    "doctype": "Lazada Push Mechanism Logs V2",
                    "push_type": "Product Push IDs error",
                    "push_msg": json.dumps(prod_response_json),
                }
            )
            add_item.insert(ignore_permissions=True)
            frappe.db.commit()
        
        outresp = response2.body.copy()
        outresp["method"] = "insert"  # to inform client script that a product was inserted
        return outresp

    else: # update the price/stock/product info only!
        # fetch stock
        it = frappe.get_doc("Item", item_obj_json["doc_name"])
        wh = frappe.get_doc("Warehouse", f"Store-Lazada - {so_company.abbr}")
        item_stock = get_stock_balance(it.name, wh.name)
        # fetch stock
        try:
            item_stock_int = int(item_stock)
        except:
            item_stock_int = 1
            
        # update price and stock first
        client = LazopClient(url, appkey ,appSecret)
        request = LazopRequest('/product/price_quantity/update')
        item_payload = f"""
            <Request>
                <Product>
                    <Skus>
                        <Sku>
                            <ItemId>{item_obj_json["laz_item_id"]}</ItemId>
                            <SkuId>{item_obj_json["laz_sku_id"]}</SkuId>
                            <Price>{item_obj_json["price"]}</Price>
                            <!--<SalePrice>900.00</SalePrice>-->
                            <!--<SaleStartDate>2017-08-08</SaleStartDate>-->
                            <!--<SaleEndDate>2017-08-31</SaleEndDate>-->
                            <Quantity>{item_stock_int}</Quantity>
                        </Sku>
                    </Skus>
                </Product>
            </Request>
        """
        request.add_api_param('payload', item_payload)
        response = client.execute(request, access_token)
        
        add_item = frappe.get_doc(
            {
                "doctype": "Lazada Push Mechanism Logs V2",
                "push_type": "updated item price",
                "push_msg": json.dumps(response.body)
            }
        )
        add_item.insert(ignore_permissions=True)
        frappe.db.commit()
        
        outresp = response.body.copy()
        outresp["method"] = "update"  # to inform client script that a product was updated
        return outresp    

@frappe.whitelist(allow_guest=True)
def lazada_info_update(item_obj=None): # ! do not use
    item_obj_json = json.loads(item_obj)

    # update price first
    client = LazopClient(url, appkey ,appSecret)
    request = LazopRequest('/product/price_quantity/update')
    item_payload = f"""
        <Request>
            <Product>
                <Skus>
                    <Sku>
                        <ItemId>{item_obj_json["laz_item_id"]}</ItemId>
                        <SkuId>{item_obj_json["laz_sku_id"]}</SkuId>
                        <Price>{item_obj_json["price"]}</Price>
                        <!--<SalePrice>900.00</SalePrice>-->
                        <!--<SaleStartDate>2017-08-08</SaleStartDate>-->
                        <!--<SaleEndDate>2017-08-31</SaleEndDate>-->
                        <!--<Quantity>30</Quantity>-->
                    </Sku>
                </Skus>
            </Product>
        </Request>
    """
    request.add_api_param('payload', item_payload)
    response = client.execute(request, access_token)
    
    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Push Mechanism Logs V2",
            "push_type": "updated item info",
            "push_msg": json.dumps(response.body)
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()


@frappe.whitelist(allow_guest=True)
def lazada_pushmech_resp(**kwargs):
    fetch_latest_access_code()
    try:
        if kwargs is not None:
            kwargs2 = frappe._dict(kwargs)

            try:
                order_status = kwargs2["data"]["order_status"]
            except:
                order_status = "unknown"

            # ! possible values:
            # --- packed, ready_to_ship, shipped, delivered ---

            add_item = frappe.get_doc(
                {
                    "doctype": "Lazada Push Mechanism Logs V2",
                    "push_type": type(kwargs2),
                    "push_msg": json.dumps(kwargs2),
                    "data_fetched": order_status,
                }
            )
            add_item.insert(ignore_permissions=True)
            frappe.db.commit()

            if order_status in ["unpaid", "pending"]:
                # TODO: fetch the product ID by calling the GetOrderItems API (use global variables instead)
                client = LazopClient(url, appkey, appSecret)
                item_request = LazopRequest("/order/items/get", "GET")
                item_request.add_api_param("order_id", kwargs2["data"]["trade_order_id"])
                item_response = client.execute(item_request, access_token)

                item_response_json = item_response.body
                # There's no need to access the *message* property anymore?

                if item_response_json["code"] != "0":
                    return dict(
                        status_code=400, body="The item request API returned an error!"
                    )

                # items = frappe.db.sql("""SELECT name,customer,shopping_platform FROM `tabSales Order` WHERE order_number='399667396843475';""", as_dict=True)
                existing_so = frappe.db.sql(
                    f"""SELECT name,customer,shopping_platform FROM `tabSales Order` WHERE order_number='{kwargs2["data"]["trade_order_id"]}';""",
                    as_dict=True,
                )

                if not existing_so:  # empty; can create new sales order
                    # fetch DEFAULT company
                    # so_company = frappe.get_doc("Company", get_default_company()).as_dict()
                    so_company = frappe.get_last_doc("Company").as_dict()
                    all_order_item_dict = []
                    all_order_item_id = []
                    all_order_item_sku = []
                    for item_product in item_response_json["data"]:
                        # regardless of the case, update the list of unique SKUs
                        all_order_item_id.append(item_product["order_item_id"])
                        if item_product["sku"] not in all_order_item_sku:
                            item_product_dict = frappe._dict(
                                {
                                    "item_code": item_product["sku"],
                                    "item_name": item_product["name"],
                                    "price_list_rate": item_product["item_price"],
                                    "description": "Test description using Lazada API",
                                    "qty": 1,
                                    "uom": "kg",
                                    "conversion_factor": 1,
                                }
                            )
                            all_order_item_dict.append(item_product_dict)
                            all_order_item_sku.append(item_product["sku"])
                        else:
                            all_order_item_dict[
                                all_order_item_sku.index(item_product["sku"])
                            ]["qty"] += 1

                    add_item = frappe.get_doc(
                        {
                            "doctype": "Sales Order",
                            "naming_series": "SAL-ORD-.YYYY.-",
                            "customer": "Lazada Customer",
                            "order_type": "Sales",
                            "transaction_date": str(date.today()),
                            "delivery_date": str(date.today() + timedelta(days=7)),
                            "custom_shipping_date": str(date.today() + timedelta(days=7)),
                            # "company": so_company.name,
                            "company": "Nature to Nurture",
                            "currency": "PHP",
                            "conversion_rate": 50.50,
                            "selling_price_list": "Standard Selling",
                            "plc_conversion_rate": 75.50,
                            # "set_warehouse": f"Store-Lazada - {so_company.abbr}",
                            "set_warehouse": f"Store-Lazada - NTN",
                            "order_number": kwargs2["data"]["trade_order_id"],
                            "order_item_number": str(all_order_item_id),
                            "shopping_platform": "Lazada",
                            "items": all_order_item_dict,
                            "status": "To Deliver and Bill",
                        }
                    )
                    add_item.insert(ignore_permissions=True)
                    frappe.db.commit()

                else:
                    add_item = frappe.get_doc(
                        {
                            "doctype": "Lazada Push Mechanism Logs V2",
                            "push_type": "duplicate sales order",
                            "push_msg": "Already have sales order for order ID in data_fetched!",
                            "data_fetched": kwargs2["data"]["trade_order_id"],
                        }
                    )

                    return dict(
                        status_code=400, body="No need to create another sales order!"
                    )

                """
                ### SINGLE ORDER CONSTRAINT 
                item_product = item_response_json["data"][0]
                # TODO: iterate through each order ITEM above, not just for first order item only!



                # tip: the code is nonzero if there is an error!
                # print(response.type) # print(response.body)

                # TODO: create a sales order
                # note: had to manually edit the code

                # return item_response_json

                add_item = frappe.get_doc({
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
                    "set_warehouse": "Store-Lazada - NTN",
                    "order_number": kwargs2["data"]["trade_order_id"],
                    "order_item_number": kwargs2["data"]["trade_order_line_id"],
                    "shopping_platform": "Lazada",
                    "items": [
                        {  # only mandatory fields listed; need to iteratively add each item
                            "item_code": item_product["sku"],
                            "item_name": item_product["name"],
                            "description": "Just a practice description using Lazada API",
                            "qty": 1,
                            "uom": "kg",
                            "conversion_factor": 1
                        }
                    ],
                    "status": "To Deliver and Bill"
                })
                add_item.insert(ignore_permissions = True)
                frappe.db.commit()
                """

            elif order_status == "packed":
                # fetch the sales order document
                existing_so = frappe.db.sql(
                    f"""SELECT name,customer,shopping_platform FROM `tabSales Order` WHERE order_number='{kwargs2["data"]["trade_order_id"]}';""",
                    as_dict=True,
                )
                
                if not existing_so:     # sales order not found; throw an error!
                    add_item = frappe.get_doc(
                        {
                            "doctype": "Lazada Push Mechanism Logs V2",
                            "push_type": "error - pushmech order_status packed",
                            "push_msg": "(see push type message)"
                        }
                    )
                    add_item.insert(ignore_permissions=True)
                    frappe.db.commit()
                    return dict(
                        status=400,
                        message="error - pushmech order_status packed (No Sales Order found!)"
                    )
                
                # add the shipping details and submit the sales order
                try:
                    existing_so_fetched = frappe.get_doc("Sales Order", existing_so[0].name)
                    existing_so_fetched_dict = existing_so_fetched.as_dict()
                    if existing_so_fetched_dict["docstatus"]==0:
                        # get the package number/s and tracking number/s via API
                        client = LazopClient(url, appkey ,appSecret)
                        request = LazopRequest('/order/items/get','GET')
                        request.add_api_param('order_id', existing_so_fetched_dict["order_number"])
                        order_items_response = client.execute(request, access_token)
                        order_items_response = order_items_response.body
                        
                        add_item = frappe.get_doc(
                            {
                                "doctype": "Lazada Push Mechanism Logs V2",
                                "push_type": "order_items_response in packed",
                                "push_msg": json.dumps(order_items_response)
                            }
                        )
                        add_item.insert(ignore_permissions=True)
                        frappe.db.commit()
                        
                        pack_numbers = []
                        track_numbers = []
                        couriers = set()
                        for a_pack in order_items_response["data"]:
                            if (a_pack["package_id"]!="" or (a_pack["package_id"] is not None)):
                                pack_numbers.append(a_pack["package_id"])
                                track_numbers.append(a_pack["tracking_code"])
                                couriers.add(a_pack["shipment_provider"])
                            
                        if(len(couriers)==1):
                            couriers = list(couriers).pop()
                        
                        # update the package number and tracking number
                        existing_so_fetched.laz_package_list = str(list(set(pack_numbers)))
                        existing_so_fetched.laz_track_list = str(list(set(track_numbers)))
                        existing_so_fetched.laz_shipment_provider = str(couriers)
                        
                        # save and submit the SO
                        existing_so_fetched.save(ignore_permissions=True)
                        existing_so_fetched.submit()
                    
                    return dict(
                        status=200,
                        message="Successfully submitted sales order after marking it as packed!"
                    )
                except Exception as e:
                    add_item = frappe.get_doc(
                        {
                            "doctype": "Lazada Push Mechanism Logs V2",
                            "push_type": "error (TRY/EXCEPT block) - pushmech order_status packed",
                            "push_msg": str(e)
                        }
                    )
                    add_item.insert(ignore_permissions=True)
                    frappe.db.commit()
                    return dict(
                        status=400,
                        message=str(e)
                    )

            elif order_status == "ready_to_ship":
                # fetch the sales order document
                existing_so = frappe.db.sql(
                    f"""SELECT name,customer,shopping_platform FROM `tabSales Order` WHERE order_number='{kwargs2["data"]["trade_order_id"]}';""",
                    as_dict=True,
                )
                
                if not existing_so:     # sales order not found; throw an error!
                    add_item = frappe.get_doc(
                        {
                            "doctype": "Lazada Push Mechanism Logs V2",
                            "push_type": "error - pushmech order_status packed",
                            "push_msg": "(see push type message)"
                        }
                    )
                    add_item.insert(ignore_permissions=True)
                    frappe.db.commit()
                    return dict(
                        status=400,
                        message="error - pushmech order_status packed (No Sales Order found!)"
                    )
                
                # create the delivery note and submit right away;
                # uses helper function technique, adopted from Shopee
                existing_so_fetched = frappe.get_doc("Sales Order", existing_so[0].name).as_dict()
                ntn_url = "https://naturetonurture.rayasolutions.store/api/method/"
                ntn_path = "nton_app.api.ship_order_new_helper"
                ntn_headers = {
                    "Authorization": "Token e2624ee0eba9640:38ecfa3de786d24",
                    "Content-Type": "application/json"
                }
                ntn_payload = {
                    "order_id": existing_so_fetched["order_number"]
                }
                ntn_params = {
                    
                }
                res = requests.post(ntn_url + ntn_path, headers=ntn_headers, params=ntn_params, json=ntn_payload)
                # parameters of ship_order_new_helper must be in payload object (where json=payload) to insert parameters correctly 
                res = json.loads(res.content)
                return res
                
                """
                try:
                    existing_so_fetched = frappe.get_doc("Sales Order", existing_so[0].name).as_dict()
                    if existing_so_fetched["delivery_status"]!="Not Delivered": # ! assume that the delivery notes are submitted for the whole order (not per item)
                        raise Exception("The current sales order already has a bound delivery note!")
                    
                    new_dn = make_delivery_note(existing_so[0].name)
                    new_dn.shipping_status = ""
                    new_dn.save()
                    new_dn.submit()        
                        
                except:
                    add_item = frappe.get_doc(
                        {
                            "doctype": "Lazada Push Mechanism Logs V2",
                            "push_type": "error (TRY/EXCEPT block) - pushmech order_status packed",
                            "push_msg": "(see push type message)"
                        }
                    )
                    add_item.insert(ignore_permissions=True)
                    frappe.db.commit()
                    return dict(
                        status=400,
                        message="error (TRY/EXCEPT block) - pushmech order_status packed (No Sales Order found!)"
                    )
                """

        else:
            add_item = frappe.get_doc(
                {
                    "doctype": "Lazada Push Mechanism Logs",
                    "push_type": "Just a sample Lazada push",
                    "push_msg": "This message should appear",
                }
            )
            frappe.db.commit()

        return add_item
    except Exception as e:
        return dict(
            status=400,
            message="Error:" + str(e)
        )
    # https://discuss.frappe.io/t/how-to-receive-data-from-a-post-request-in-frappe/36256/3

    # also check ff link to know how pushmech works:
    ### https://open.lazada.com/apps/doc/doc?nodeId=29526&docId=120168


@frappe.whitelist(allow_guest=True)
def ship_order_new_helper(order_id="TESTBATCHQUAL12345", sandbox=False):
    """
        Holds the actual implementation of creating a new delivery note.
        Lazada version...
        [Feb. 08] Updates the sales order -- populate the package number and tracking number
            - moved to the packed status function
    """
    existing_so = frappe.db.sql(
        f"SELECT name,customer,shopping_platform FROM `tabSales Order` WHERE order_number='{order_id}';",
        as_dict=True
    )
    
    if not existing_so:     # sales order not found; throw an error!
        return dict(
            status=400,
            message="error - Lazada pushmech order_status (No Sales Order found!)"
        )
    
    # submit the sales order and create the delivery note
    try:
        existing_so_fetched = frappe.get_doc("Sales Order", existing_so[0].name)
        existing_so_fetched_dict = existing_so_fetched.as_dict()
        if existing_so_fetched_dict["docstatus"]==0:
            # get the package number/s and tracking number/s via API
            client = LazopClient(url, appkey ,appSecret)
            request = LazopRequest('/order/items/get','GET')
            request.add_api_param('order_id', existing_so_fetched_dict["order_number"])
            order_items_response = client.execute(request, access_token)
            order_items_response = order_items_response.body
            
            # TODO: uncomment when done with sandbox products
            # pack_numbers = []
            # track_numbers = []
            # couriers = set()
            # for a_pack in order_items_response["data"]:
            #     if (a_pack["package_id"]!="" or (a_pack["package_id"] is not None)):
            #         pack_numbers.append(a_pack["package_id"])
            #         track_numbers.append(a_pack["tracking_code"])
            #         couriers.add(a_pack["shipment_provider"])
                
            # if(len(couriers)==1):
            #     couriers = list(couriers).pop()
            
            # # update the package number and tracking number
            # existing_so_fetched.laz_package_list = str(list(set(pack_numbers)))
            # existing_so_fetched.laz_track_list = str(list(set(track_numbers)))
            # existing_so_fetched.laz_shipment_provider = str(couriers)
            
            # save and submit the SO
            existing_so_fetched.save(ignore_permissions=True)
            existing_so_fetched.submit()
            
        
        if existing_so_fetched_dict["delivery_status"]!="Not Delivered": # ! assume that the delivery notes are submitted for the whole order (not per item)
            raise Exception("LAZADA API - The current sales order already has a bound delivery note!")
        
        
        auto_submit = True
        
        # TODO: check if an existing DRAFT delivery note exists to avoid duplicates
        new_dn = make_delivery_note(existing_so[0].name)
        new_dn.shipping_status = ""
        new_dn_dict = new_dn.as_dict()
        print("new_dn_dict")
        print(new_dn_dict)
        
        
        # iterate through the items...
        for an_item in new_dn_dict["items"]:
            an_item_doc = frappe.get_doc("Item", an_item["item_code"])
            print("an_item_doc.inspection_required_before_delivery:",an_item_doc.inspection_required_before_delivery)
            if an_item_doc.inspection_required_before_delivery:
                auto_submit = False
                break
        
        new_dn.insert()
        frappe.db.commit()

        new_dn.save()
        # # check if Item's inspection_required_before_delivery is checked. If yes, do NOT submit first...
        if auto_submit:
            new_dn.submit()

    except Exception as e:
        return dict(
            status=400,
            message=f"Lazada error (TRY/EXCEPT block) - {str(e)}"
        )
    else:
        # Ensure that permission checks are restored to their original state
        return dict(
            status=200,
            message="Finished Lazada delivery note process!"
        )


@frappe.whitelist(allow_guest=True)
def test_fetch_so():
    existing_so_fetched = frappe.get_doc("Sales Order", "SAL-ORD-2024-03652")
    print(existing_so_fetched.as_dict())
    existing_so_fetched.save(ignore_permissions=True)
    existing_so_fetched.submit()
    return dict(
        status=200,
        message="Successfully submitted sales order after marking it as packed!"
    )
    
@frappe.whitelist(allow_guest=True)
def lazada_order_pack(req_params):
    fetch_latest_access_code()
    req_params_json = json.loads(req_params)
    pack_req = {}   # parent dict

    # "order_item_list": [int(x) for x in req_params_json["order_item_ids"].strip('][').split(', ')],   # or [int(x) for x in req_params_json["order_item_ids"]]
    pack_order_list = [{
        "order_item_list": [int(x) for x in (req_params_json["order_item_ids"].strip('][').split(', '))],
        "order_id": int(req_params_json["order_number"])
    }]
    pack_req["delivery_type"] = "dropship"
    pack_req["shipping_allocate_type"] = "TFS"
    pack_req["pack_order_list"] = pack_order_list

    # call the API
    client = LazopClient(url, appkey ,appSecret)
    request = LazopRequest('/order/fulfill/pack')
    request.add_api_param('packReq', json.dumps(pack_req))
    response = client.execute(request, access_token)

    pack_response_json = response.body

    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Push Mechanism Logs V2",
            "push_type": "Packing Order NEW API",
            "push_msg": json.dumps(pack_response_json),
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()
    
    # obtain the list of packages
    pack_numbers = []
    track_numbers = []
    couriers = set()
    for a_pack in pack_response_json["result"]["data"]["pack_order_list"][0]["order_item_list"]:
        pack_numbers.append(a_pack["package_id"])
        track_numbers.append(a_pack["tracking_number"])
        couriers.add(a_pack["shipment_provider"])

    if(len(couriers)==1):
        couriers = list(couriers).pop()
    
    return dict(
        package_list = str(pack_numbers),
        track_list = str(track_numbers),
        shipment_provider = str(couriers)
    )
    # retrieve packageId afterwards...

    # ! old code below for other pack API
    client = LazopClient(url, appkey, appSecret)
    request = LazopRequest("/order/pack")
    request.add_api_param("shipping_provider", req_params_json["shipment_provider"])
    request.add_api_param("delivery_type", req_params_json["delivery_type"])
    request.add_api_param("order_item_ids", req_params_json["order_item_ids"])
    response = client.execute(request, access_token)

    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Push Mechanism Logs V2",
            "push_type": "Manual Pack Update",
            "push_msg": json.dumps(response.body),
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()

    return response.body



@frappe.whitelist(allow_guest=True)
def lazada_get_shipment_providers():
    fetch_latest_access_code()
    client = LazopClient(url, appkey ,appSecret)
    request = LazopRequest('/shipment/providers/get','GET')
    response = client.execute(request, access_token)
    shipment_resp_json = response.body

    # logs
    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Push Mechanism Logs V2",
            "push_type": "Shipment Providers List - Lazada",
            "push_msg": json.dumps(shipment_resp_json)
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()

    return shipment_resp_json["data"]["shipment_providers"]

@frappe.whitelist(allow_guest=True)
def lazada_delivery_rts(req_params):  # delivery note just created; trigger ready-to-ship
    fetch_latest_access_code()
    req_params_json = json.loads(req_params)

    packages_value = []
    packages_list_parsed =  req_params_json["laz_package_list"].strip('][').replace("'","").split(', ')
    for a_package in packages_list_parsed:
        packages_value.append(dict(
            package_id=a_package
        ))
    
    packages_dict = {
        "packages": packages_value
    }

    client = LazopClient(url, appkey ,appSecret)
    request = LazopRequest('/order/package/rts')
    request.add_api_param('readyToShipReq', json.dumps(packages_dict))
    # example payload: '{\"packages\":[{\"package_id\":\"FP234234\"},{\"package_id\":\"FP234234\"}]}
    response = client.execute(request, access_token)
    
    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Push Mechanism Logs V2",
            "push_type": "Updated result in lazada_delivery_rts",
            "push_msg": json.dumps(response.body),
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()

    return response.body
    
    return
    # ! old RTS code below

    """items = frappe.db.sql(
        f"SELECT name,customer,shopping_platform,order_item_number FROM `tabSales Order` WHERE order_number='{req_params_json["order_num"]}';",
        as_dict=True,
    )
    # ! change variables above where necessary

    if items[0]["shopping_platform"] != "Lazada":
        add_item = frappe.get_doc(
            {
                "doctype": "Lazada Push Mechanism Logs V2",
                "push_type": "SQL Error -- Not Lazada",
                "push_msg": json.dumps(items[0]),
                "data_fetched": items[0]["shopping_platform"],
            }
        )
        add_item.insert(ignore_permissions=True)
        frappe.db.commit()

        return dict(status_code=400, body="Not a Lazada order!")"""

    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Push Mechanism Logs V2",
            "push_type": "reqs_param in lazada_delivery_rts",
            "push_msg": json.dumps(req_params_json),
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()

    client = LazopClient(url, appkey, appSecret)
    request = LazopRequest("/order/rts")
    request.add_api_param("delivery_type", "dropship")
    request.add_api_param("order_item_ids", str(req_params_json["order_item_number"]))
    request.add_api_param("shipment_provider", str(req_params_json["laz_shipment_provider"]))
    request.add_api_param("tracking_number", str(req_params_json["laz_tracking_number"]))
    response = client.execute(request, access_token)

    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Push Mechanism Logs V2",
            "push_type": "GetOrderItems Update in lazada_delivery_rts",
            "push_msg": json.dumps(response.body),
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()

    return response.body


@frappe.whitelist(allow_guest=True)
def lazada_print_awb(req_params):   # ! Do not Use!
    fetch_latest_access_code()
    req_params_json = json.loads(req_params)

    client = LazopClient(url, appkey, appSecret)
    item_request = LazopRequest("/order/items/get", "GET")
    item_request.add_api_param("order_id", req_params_json["order_num"])
    item_response = client.execute(item_request, access_token)

    item_response_json = item_response.body
    # There's no need to access the *message* property anymore

    if item_response_json["code"] != "0":
        add_item = frappe.get_doc(
            {
                "doctype": "Lazada Push Mechanism Logs V2",
                "push_type": "GetOrderItems Error in lazada_print_awb",
                "push_msg": json.dumps(item_response_json),
            }
        )
        add_item.insert(ignore_permissions=True)
        frappe.db.commit()

        return dict(status_code=400, body=item_response_json)

    item_product = item_response_json["data"][0]

    client = LazopClient(url, appkey, appSecret)
    request = LazopRequest("/order/document/awb/html/get", "GET")
    request.add_api_param("order_item_ids", str(item_product["order_item_id"]))
    # request.add_api_param('order_item_ids', "[" + str(item_product["order_item_id"]) + "]")
    response = client.execute(request, access_token)

    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Push Mechanism Logs V2",
            "push_type": "Manual Pack Update",
            "push_msg": json.dumps(response.body),
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()

    # TODO: remove temporary --> return dummy HTML only
    return "<!DOCTYPE html><html><body><h1>My First Heading</h1><p>My first paragraph.</p></body></html>"

    if response.body.code != "0":
        if response.body.message.count("*") > 10:
            return "<!DOCTYPE html><html><body><h1>My First Heading</h1><p>My first paragraph.</p></body></html>"

    return response.body


@frappe.whitelist(allow_guest=True)
def lazada_add_qty(req_params):
    # TODO: finish add_qty function onsubmit of Stock Entry
    fetch_latest_access_code()
    req_params_json = json.loads(req_params)
    # req_params parameters
    ### products: array of dict/objects with properties: item_code, qty,
    ### products (cont.): t_warehouse (target warehouse; must match Lazada's), s_warehouse (source warehouse; take into account when deducting stock)
    ### company: (used Nature to Nurture as example)
    ### stock_entry_type: must be equal to "Material Receipt" or "Material Transfer"

    if req_params_json["stock_entry_type"] not in [
        "Material Receipt",
        "Material Transfer",
    ]:
        return dict(
            status_code=400,
            body="Stock entry submission was not Material Receipt nor Material Transfer!",
        )

    draft_payload = "<Request><Product><Skus>"

    for a_product in req_params_json["products"]:
        if (
            req_params_json["company"] == "Nature to Nurture"
            and a_product["t_warehouse"] == "Store-Lazada - NTN"
        ):
            draft_payload += f"""
                <Sku>
                    <SellerSku>{a_product["item_code"]}</SellerSku>
                    <SellableQuantity>{a_product["qty"]}</SellableQuantity>
                </Sku>
            """
    draft_payload += "</Skus></Product></Request>"

    client = LazopClient(url, appkey, appSecret)
    request = LazopRequest("/product/stock/sellable/adjust")
    request.add_api_param("payload", draft_payload)
    response = client.execute(request, access_token)
    stock_response_json = response.body

    if stock_response_json["code"] != "0":
        add_item = frappe.get_doc(
            {
                "doctype": "Lazada Push Mechanism Logs V2",
                "push_type": "ERROR lazada_add_qty",
                "push_msg": json.dumps(stock_response_json),
            }
        )
        add_item.insert(ignore_permissions=True)
        frappe.db.commit()

        return dict(status_code=400, body="The item request API returned an error!")

    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Push Mechanism Logs V2",
            "push_type": "lazada_add_qty Result",
            "push_msg": json.dumps(stock_response_json),
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()

    return add_item


@frappe.whitelist(allow_guest=True)
def fetch_latest_access_code():  # callback URL which receives the auth code
    new_si_fetched = frappe.get_last_doc("Lazada Credentials")
    global access_token, so_company
    access_token = new_si_fetched.access_token
    # return new_si_fetched
    # print("Check")
    so_company = frappe.get_doc("Company", get_default_company()).as_dict()
    # print(so_company)
    if (so_company is None):
        # print("2nd attempt")
        so_company = frappe.get_last_doc("Company").as_dict()
        # print(json.dumps(so_company))


@frappe.whitelist(allow_guest=True)
def last_product():  # callback URL which receives the auth code
    new_si_fetched = frappe.get_last_doc("Item")
    return new_si_fetched


@frappe.whitelist(allow_guest=True)
def lazada_test_getorder():
    # def lazada_test_function(item_obj):
    # returns item_obj json as string
    fetch_latest_access_code()
    client = LazopClient(url, appkey, appSecret)
    item_request = LazopRequest("/order/items/get", "GET")
    item_request.add_api_param("order_id", "744646237933894")
    item_response = client.execute(item_request, access_token)

    return item_response.body


@frappe.whitelist(allow_guest=True)
def lazada_test_function():
    # def lazada_test_function(item_obj):
    # returns item_obj json as string
    fetch_latest_access_code()
    # client = LazopClient(url, appkey, appSecret)
    # item_request = LazopRequest("/order/items/get", "GET")
    # item_request.add_api_param("order_id", "402219109944621")
    # item_response = client.execute(item_request, access_token)

    client = LazopClient(url, appkey, appSecret)
    request = LazopRequest("/orders/get", "GET")
    request.add_api_param("update_before", "2024-02-10T16:00:00+08:00")
    request.add_api_param("sort_direction", "DESC")
    request.add_api_param("offset", "0")
    request.add_api_param("limit", "10")
    request.add_api_param("update_after", "2017-02-10T09:00:00+08:00")
    request.add_api_param("sort_by", "updated_at")
    # request.add_api_param('created_before', '2018-02-10T16:00:00+08:00')
    # request.add_api_param('created_after', '2017-02-10T09:00:00+08:00')
    # request.add_api_param('status', 'shipped')
    item_response = client.execute(request, access_token)
    # print(response.type)
    # print(response.body)

    return item_response.body
