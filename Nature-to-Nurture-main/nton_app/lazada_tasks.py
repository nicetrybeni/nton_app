import frappe
from frappe.utils.pdf import get_pdf
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
from erpnext.accounts.doctype.payment_request.payment_request import (
    make_payment_request,
    make_payment_entry,
)
from lazop_sdk import LazopClient, LazopRequest
import json
from erpnext.stock.utils import get_stock_balance
from erpnext import get_default_company
from base64 import b64encode, b64decode
from datetime import date,timedelta


### Lazada API Variables
# url = "https://api.lazada.com.my/rest"
url = "https://api.lazada.com.ph/rest"
appkey = 126275
appSecret = "7IrbxBBHReeC3DaApuBX13dFtu4BZtjT"
access_token = "50000000b23gyMlApVRydfyn2GhPgsuiacj19c07b24q3LRWcngQG4mRw9JLOSUe"
so_company = None


@frappe.whitelist(allow_guest=True)
def test_cron():
    cron()


# Lazada 3AM Batch run
def cron():
    fetch_latest_access_code()
    print("Cron check")
    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Push Mechanism Logs V2",
            "push_type": "Cron Job Check",
            "push_msg": "Check test cronjob only",
        }
    )
       
    # ! fetch pending sales orders lacking a sales invoice
    # so_billable = frappe.db.sql("""SELECT name,customer,order_number FROM `tabSales Order` WHERE order_number='749038572945115' AND shopping_platform='Lazada';""", as_dict=True)
    so_billable = frappe.db.sql(
        """SELECT name,customer,order_number FROM `tabSales Order` WHERE status='To Bill' AND shopping_platform='Lazada';""",
        as_dict=True,
    )
    print("Number of billables:",len(so_billable))
    
    so_skippable = False
    for so_single in so_billable:
        so_skippable = False
        print("-------------")
        
        # ! fetch transactions
        client = LazopClient(url, appkey ,appSecret)
        request = LazopRequest('/finance/transaction/details/get','GET')
        request.add_api_param('offset', '0')
        request.add_api_param('trans_type', '-1')
        request.add_api_param('trade_order_id', so_single["order_number"])     # to change the order number here
        request.add_api_param('limit', '500')
        request.add_api_param('start_time', str(date.today() + timedelta(days=-7)))
        request.add_api_param('end_time', str(date.today()))
        transac_response = client.execute(request, access_token)
        transac_response_json = transac_response.body
        
        print("transac_response_json")
        print(transac_response_json)
        
        if(len(transac_response_json["data"])==0):      # not yet handled; can skip this invoice first
            continue
        
        # add up all costs
        sum_expenses = 0
        for a_transac in transac_response_json["data"]:
            # sum_expenses += float(a_transac["amount"]
            if(a_transac["paid_status"]!="paid"):                       # do not create the sales invoice first; stop right away
                so_skippable = True
                break
            if (float(a_transac["amount"])<0):                          # seller fees
                sum_expenses += float(a_transac["amount"])
            elif (a_transac["fee_name"] not in ["Item Price Credit"]):  # rebates?
                sum_expenses += float(a_transac["amount"])
        
        # if detected an unpaid entry, skip the SO
        if so_skippable:
            continue
        
        # ? save sum_expenses later for taxes. Use format: res = "{:.2f}".format(fnum)
        
        new_si = make_sales_invoice(so_single["name"], ignore_permissions=True)

        # client = LazopClient(url, appkey, appSecret)
        # request = LazopRequest("/order/get", "GET")
        # request.add_api_param("order_id", so_single["order_number"])
        # response = client.execute(request, access_token)
        # response_order_json = response.body
        
        print(so_single["name"])
        print("new_si name:")
        print(new_si.taxes)
        new_si.insert()

        new_si_fetched = frappe.get_last_doc("Sales Invoice")
        temp_company = frappe.get_doc("Company", new_si_fetched.company).as_dict()

        sales_and_tax_single = frappe.new_doc("Sales Taxes and Charges")
        sales_and_tax_single.update(
            {
                "charge_type": "Actual",
                "account_head": f"Miscellaneous Expenses - {temp_company.abbr}",
                "description": "Miscellaneous Expenses",
                "cost_center": f"Main - {temp_company.abbr}",
                "account_currency": "PHP",
                "tax_amount": sum_expenses,
                "parenttype": "Sales Invoice",
                "parent": new_si_fetched.name,
                "parentfield": "taxes",
                "idx": 0,
            }
        )
        # 'tax_amount': float(response_order_json["data"]["shipping_fee"]),

        # ! duplicate save() and append below; choose only one
        # ! the save() doesn't work?
        # sales_and_tax_single.save()
        new_si.taxes.append(sales_and_tax_single)
        
        print(new_si.status)
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

    """
    resp = requests.get("https://api.lazada.com.ph/rest/orders/get?sort_direction=DESC&offset=0&created_after=1999-10-10T16%3A00%3A00%2B08%3A00&limit=30&sort_by=updated_at&status=ready_to_ship&app_key=126275&sign_method=sha256&access_token=50000600621qhqtLfuBiCwVuR9b2otcpQ18526e15h0rCYEjrgkTuefILEHM1Ppg&timestamp=1695839744760&sign=7AD8CEC1F07333937DB359F536DD745F49657B658AFFFC0F9487E5F28B34A9B8")
    ret = json.loads(resp.content)
    all_orders = ret["data"]["orders"]
    print("Number of orders ready:",ret["data"]["countTotal"])
    """

    add_item.insert(ignore_permissions=True)
    frappe.db.commit()


@frappe.whitelist(allow_guest=True)
def create_awb_pdf(order_num):
    fetch_latest_access_code()
    so_sql = frappe.db.sql(
        f"""SELECT name,shopping_platform,order_item_number,laz_package_list FROM `tabSales Order` WHERE order_number='{order_num}';""",
        as_dict=True,
    )
    so_awb = so_sql[0]
    
    # generate the parameters first
    packages_value = []
    packages_list_parsed =  so_awb["laz_package_list"].strip('][').replace("'","").split(', ')
    for a_package in packages_list_parsed:
        packages_value.append(dict(
            package_id=a_package
        ))
    
    get_document_req = dict(
        doc_type = "PDF",
        packages = packages_value,
        print_item_list = True
    )
    # optional parameter: print_item_list == True (for more details in Item List) or False (minimalist)
    
    
    
    client = LazopClient(url, appkey, appSecret)
    request = LazopRequest('/order/package/document/get')
    request.add_api_param('getDocumentReq', json.dumps(get_document_req))
    response = client.execute(request, access_token)
    
    awb_response = response.body
    
    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Push Mechanism Logs V2",
            "push_type": "PrintAWB New Result",
            "push_msg": json.dumps(response.body),
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return awb_response["result"]["data"]["pdf_url"]

    request = LazopRequest("/order/document/awb/html/get", "GET")
    request.add_api_param("order_item_ids", so_awb["order_item_number"])
    response = client.execute(request, access_token)
    awb_response = response.body
    # print(response.type)
    # print(response.body)

    # file = frappe.get_doc("File", name)
    if awb_response["code"] != "0":
        add_item = frappe.get_doc(
            {
                "doctype": "Lazada Push Mechanism Logs V2",
                "push_type": "create_awb_pdf error in lazada_tasks.py",
                "push_msg": json.dumps(awb_response),
            }
        )
        add_item.insert(ignore_permissions=True)
        frappe.db.commit()

        return dict(
            status_code=400,
            body="The create_awb_pdf method detected an error in the AWB response!",
        )

    # building the HTML response
    html_resp = awb_response["data"]["document"]["file"]
    if html_resp.count("*****") > 20:  # most likely masked
        html_resp = f"<!DOCTYPE html><html><body><h1>My Print-ready AWB (masked)</h1><p>Insert print-ready airway bill with order number {order_num}</p></body></html>"

    # verify whether base-encoded or not
    # if b64encode(b64decode(html_resp)) == html_resp:  # is still in base64 format
    #   html_resp = b64decode(html_resp)

    frappe.response.filename = f"awb_{order_num}_pdf.pdf"
    frappe.response.filecontent = get_pdf(html_resp)
    frappe.response.type = "pdf"  # changed from "download"
    frappe.response.display_content_as = "inline"


@frappe.whitelist(allow_guest=True)
def clean_logs():
    count = 0
    doclist = frappe.db.get_all("Lazada Push Mechanism Logs V2")
    for doc in doclist:
        frappe.db.delete("Lazada Push Mechanism Logs V2", doc.name)
    """
    for a_log in frappe.get_list('Lazada Push Mechanism Logs V2'):
        a_log = frappe.get_doc('Lazada Push Mechanism Logs V2', a_log.name)
        a_log.delete()
        count += 1
        # if count>1000:
        #     break
    """
    frappe.db.commit()
    return dict(
        status_code=200,
        body="Clean logs success!",
        list_length=len(frappe.get_list("Lazada Push Mechanism Logs V2")),
    )


# shop authorization, example url
# https://auth.lazada.com/oauth/authorize?response_type=code&force_auth=true&redirect_uri=https://naturetonurture.rayasolutions.store/&client_id=126275
# https://auth.lazada.com/oauth/authorize?response_type=code&force_auth=true&redirect_uri=https://naturetonurture.rayasolutions.store/api/method/nton_app.lazada_tasks.generate_token&client_id=126275
# https://naturetonurture.rayasolutions.store/api/method/nton_app.lazada_tasks.generate_token
@frappe.whitelist(allow_guest=True)
def generate_token(code):  # callback URL which receives the auth code
    client = LazopClient("https://auth.lazada.com/rest", appkey, appSecret)
    request = LazopRequest("/auth/token/create")
    request.add_api_param("code", str(code))
    response = client.execute(request)

    response_json = response.body

    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Credentials",
            "access_token": response_json["access_token"],
            "access_expiry": response_json["expires_in"],
            "refresh_token": response_json["refresh_token"],
            "refresh_expiry": response_json["refresh_expires_in"],
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()

    return dict(status=200, message="Authorization success!")


@frappe.whitelist(allow_guest=True)
def fetch_latest_access_code():  # callback URL which receives the auth code
    new_si_fetched = frappe.get_last_doc("Lazada Credentials")
    global access_token, so_company
    access_token = new_si_fetched.access_token
    # return new_si_fetched
    so_company = frappe.get_last_doc("Company")
    # so_company = frappe.get_doc("Company", get_default_company()).as_dict()
    # if so_company is None: # TODO: Edit
    #     so_company = frappe.get_last_doc("Company")


@frappe.whitelist(allow_guest=True)
def generate_new_token():
    new_si_fetched = frappe.get_last_doc("Lazada Credentials")
    # global access_token
    old_refresh_token = new_si_fetched.refresh_token
    client = LazopClient("https://auth.lazada.com/rest", appkey, appSecret)
    request = LazopRequest("/auth/token/refresh")
    request.add_api_param("refresh_token", old_refresh_token)
    response = client.execute(request)
    response_json = response.body
    if response_json["code"] != "0":
        return dict(
            status_code=400,
            body="The generate_new_token API returned an error!",
            message=response.body,
        )

    add_item = frappe.get_doc(
        {
            "doctype": "Lazada Credentials",
            "access_token": response_json["access_token"],
            "access_expiry": response_json["expires_in"],
            "refresh_token": response_json["refresh_token"],
            "refresh_expiry": response_json["refresh_expires_in"],
        }
    )
    add_item.insert(ignore_permissions=True)
    frappe.db.commit()

    return dict(status_code=200, body="Successful generate_new_token!")


@frappe.whitelist(allow_guest=True)
def test_get_item():
    fetch_latest_access_code()
    client = LazopClient(url, appkey, appSecret)
    request = LazopRequest("/product/item/get", "GET")
    request.add_api_param("item_id", "4239221282")
    response = client.execute(request, access_token)
    return json.dumps(response.body) + access_token


@frappe.whitelist(allow_guest=True)
def test_update_stock():
    fetch_latest_access_code()
    item_id = "3969698065"
    sku_id = "22704186189"
    it = frappe.get_doc("Item", "Lazada Test Item")
    wh = frappe.get_doc("Warehouse", f"Store-Lazada - {so_company.abbr}")
    item_stock = get_stock_balance(it.name, wh.name)
    
    # fetch stock
    try:
        item_stock_int = int(item_stock)
    except:
        item_stock_int = 1

    print("Item Stock:")
    print(item_stock_int)
    
    # set up payload
    item_req_xml = f"""
        <Request>
            <Product>
                <ItemId>{item_id}</ItemId>
                <Skus>
                    <Sku>
                        <SkuId>{sku_id}</SkuId>
                        <SellableQuantity>{item_stock_int}</SellableQuantity>
                    </Sku>
                </Skus>
            </Product>
        </Request>
    """
    info = {
        "item_id": item_id,
        "sku_id": sku_id,
        "stock": item_stock_int,
        "name": it.name,
        "wh": wh.name,
    }
    # stock = get_stock_balance(a_laz_item['item_name'], wh)

    try:
        # send the request
        client = LazopClient(url, appkey, appSecret)
        request = LazopRequest("/product/stock/sellable/update")
        request.add_api_param("payload", item_req_xml)
        response = client.execute(request, access_token)
        add_item = frappe.get_doc(
            {
                "doctype": "Lazada Push Mechanism Logs V2",
                "push_type": "item update",
                "push_msg": json.dumps(response.body)
                + json.dumps(response.type)
                + str(info),
            }
        )
        add_item.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        add_item = frappe.get_doc(
            {
                "doctype": "Lazada Push Mechanism Logs V2",
                "push_type": "error in update_stock",
                "push_msg": e,
            }
        )
        add_item.insert(ignore_permissions=True)
        frappe.db.commit()
    finally:
        return add_item


@frappe.whitelist(allow_guest=True)
def update_stock():
    fetch_latest_access_code()

    laz_items = frappe.db.sql(
        """SELECT name, item_code, laz_item_id, laz_sku_id FROM `tabItem` WHERE price > '';""",
        as_dict=True,
    )
    wh = frappe.get_doc("Warehouse", f"Store-Lazada - {so_company.abbr}")
    for a_laz_item in laz_items:
        it = frappe.get_doc("Item", a_laz_item["item_code"])
        item_stock = get_stock_balance(it.name, wh.name)

        try:
            item_stock_int = int(item_stock)
        except:
            item_stock_int = 1

        # set up payload
        item_req_xml = f"""
            <Request>
                <Product>
                    <ItemId>{a_laz_item['laz_item_id']}</ItemId>
                    <Skus>
                        <Sku>
                            <SkuId>{a_laz_item['laz_sku_id']}</SkuId>
                            <SellableQuantity>{item_stock_int}</SellableQuantity>
                        </Sku>
                    </Skus>
                </Product>
            </Request>
        """

        # stock = get_stock_balance(a_laz_item['item_name'], wh)

        try:
            # send the request
            client = LazopClient(url, appkey, appSecret)
            request = LazopRequest("/product/stock/sellable/update")
            request.add_api_param("payload", item_req_xml)
            response = client.execute(request, access_token)
            print(
                "successfully saved stock",
                item_stock_int,
                "for item",
                it.name,
                "with itemID",
                a_laz_item["laz_item_id"],
                "and skuID",
                a_laz_item["laz_sku_id"],
            )
        except Exception as e:
            add_item = frappe.get_doc(
                {
                    "doctype": "Lazada Push Mechanism Logs V2",
                    "push_type": "error in update_stock",
                    "push_msg": e,
                }
            )
            add_item.insert(ignore_permissions=True)
            frappe.db.commit()
            print("failed to update product stock")
    return response.body
    # print(response.type)
    # print(response.body)


@frappe.whitelist(allow_guest=True)
def get_item_test():
    fetch_latest_access_code()

    laz_items = frappe.get_doc("Item", "YCD SAMPLE ITEM")
    return laz_items


@frappe.whitelist(allow_guest=True)
def test_company():
    fetch_latest_access_code()
    print(so_company.abbr)
    return so_company
