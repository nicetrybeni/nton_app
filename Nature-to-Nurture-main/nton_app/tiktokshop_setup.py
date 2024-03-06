import requests
import json
import frappe

def unix_to_datetime(unix):
    NUM_OF_SEC_IN_DAYS = 86400
    return frappe.utils.add_days(frappe.utils.get_datetime("1970-01-01"), int(unix) / NUM_OF_SEC_IN_DAYS)

def is_json_key_present(json, key):
    try:
        buf = json[key]
    except KeyError:
        return False

    return True

@frappe.whitelist(allow_guest=True)
def tiktokshop_insert_token():
    return token_processing(sandbox=False)

@frappe.whitelist(allow_guest=True)
def tiktokshop_insert_token_sb():
    return token_processing(sandbox=True)
    

def token_processing(sandbox=False):
    req = frappe.form_dict

    if is_json_key_present(frappe.form_dict, "env"):
        if req["env"] == "test":
            return {
                'content' : frappe.form_dict,
            }

    doc = frappe.get_doc({
        'doctype' : 'Tiktok Auth',
        'tiktok_content' : str(frappe.form_dict),
    })
    doc.insert()
    frappe.db.commit()

    #ERPNext_NTN
    path = "/api/v2/token/get"
    app_key = "6a8u5auuqugdu"
    app_secret = "cfa8480cdb0288ead599611f2e4fcaf95dfe3616"
    domain =""
    
    if sandbox:
        domain = "https://auth-sandbox.tiktok-shops.com"
    else:
        domain = "https://auth.tiktok-shops.com"


    auth_code = req["code"]
    state = req["state"]
    grant_type = "authorized_code"

    link = domain + path
    payload = {
        'app_key' : app_key,
        'auth_code' : auth_code,
        'app_secret' : app_secret,
        'grant_type' : grant_type,
    }
    tiktok_res = requests.get(link,payload)
    
    tiktok_data = (tiktok_res.json())

    # doc = frappe.get_doc({
    #     'doctype' : 'Tiktok Auth',
    #     'tiktok_content' : str(tiktok_data) + str(tiktok_res.url),
    # })
    # doc.insert()
    # frappe.db.commit()

    
    if is_json_key_present(frappe.form_dict, "env"):
        if req["env"] == "url":
            return tiktok_data

    tiktok_data = tiktok_data["data"]
    access_token = tiktok_data["access_token"]
    refresh_token = tiktok_data["refresh_token"]
    access_expiry = frappe.utils.get_datetime(unix_to_datetime(tiktok_data["access_token_expire_in"]))
    refresh_expiry = frappe.utils.get_datetime(unix_to_datetime(tiktok_data["refresh_token_expire_in"]))

    doc = frappe.get_doc({
        'doctype' : 'Tiktok Credentials',
        'access_token' : access_token,
        'access_expiry' : (access_expiry),
        'refresh_token' : refresh_token,
        'refresh_expiry' : (refresh_expiry),
    })
    doc.insert()
    frappe.db.commit()

    return {
        'code' : 200
    }

@frappe.whitelist(allow_guest=True)
def refresh_token(sandbox=False):
    
    #ERPNext_NTN
    path = "/api/v2/token/refresh"
    app_key = "6a8u5auuqugdu"
    app_secret = "cfa8480cdb0288ead599611f2e4fcaf95dfe3616"

    if sandbox:
        name = 'Sandbox Token'
        credentials = frappe.get_doc('Tiktok Credentials', name)
        domain = 'https://auth-sandbox.tiktok-shops.com'
        
    else:
        name = 'Prod Token'
        credentials = frappe.get_doc('Tiktok Credentials', name)
        domain = 'https://auth.tiktok-shops.com'

    refresh_token = credentials.refresh_token
    grant_type = "refresh_token"

    link = domain + path
    payload = {
        'app_key' : app_key,
        'app_secret' : app_secret,
        'refresh_token' : refresh_token,
        'grant_type' : grant_type,
    }
    
    doc = frappe.get_doc({
        'doctype' : 'Tiktok Webhook',
        'content' : str([payload]),
        'tags' : 'refresh payload'
    })
    doc.insert()
    frappe.db.commit()

    tiktok_res = requests.get(link,payload)
    
    tiktok_data = (tiktok_res.json())

    tiktok_data = tiktok_data["data"]
    access_token = tiktok_data["access_token"]
    refresh_token = tiktok_data["refresh_token"]
    access_expiry = frappe.utils.get_datetime(unix_to_datetime(tiktok_data["access_token_expire_in"]))
    refresh_expiry = frappe.utils.get_datetime(unix_to_datetime(tiktok_data["refresh_token_expire_in"]))

    # doc = frappe.get_doc({
    #     'doctype' : 'Tiktok Credentials',
    #     'access_token' : access_token,
    #     'access_expiry' : (access_expiry),
    #     'refresh_token' : refresh_token,
    #     'refresh_expiry' : (refresh_expiry),
    #     'name' : name
    # })
    credentials.access_token = access_token
    credentials.access_expiry = access_expiry
    credentials.refresh_token = refresh_token
    credentials.refresh_expiry = refresh_expiry
    credentials.save()
    # frappe.db.commit()

    return {
        'code' : 200
    }

