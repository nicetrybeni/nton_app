import frappe
import requests
from ecommerce_integrations.shopify.utils import create_shopify_log

HOST_SB = "https://n2n-sandbox.myshopify.com"

@frappe.whitelist()
def update_shopify_fulfillment(order_id):
    path = '/admin/api/2024-01/fulfillments/{}/update_tracking.json'.format(order_id)
    headers = {
        'X-Shopify-Access-Token': get_access_token(),
        'Content-Type': 'application/json',
    }

    json_data = {
        'fulfillment': {
            'tracking_info': {
                'company': '-',
                'number': '',
            },
        },
    }
    response = requests.post(
        HOST_SB + path,
        headers=headers,
        json=json_data,
    )

    create_shopify_log(response_data=response,method='update_shopify_fulfillment',message=response.text)

@frappe.whitelist()
def get_fulfillment(order_id):
    path = '/admin/api/2024-01/orders/{}/fulfillments/255858046.json'.format(order_id)
    headers = {
        'X-Shopify-Access-Token': get_access_token(),
    }

    json_data = {
        'fulfillment': {
            'tracking_info': {
                'company': '-',
                'number': '',
            },
        },
    }
    response = requests.post(
        HOST_SB + path,
        headers=headers,
        json=json_data,
    )

    create_shopify_log(response_data=response,method='update_shopify_fulfillment',message=response.text)

@frappe.whitelist(allow_guest=True)
def get_fulfillment_orders(order_id):
    path = '/admin/api/2024-01/orders/{}/fulfillment_orders.json'.format(order_id)
    headers = {
        'X-Shopify-Access-Token': get_access_token(),
    }
    response = requests.get(
        HOST_SB + path,
        headers=headers,
    )

    create_shopify_log(method='get_fulfillment_orders',message=str(response.text))

@frappe.whitelist(allow_guest=True)
def get_unfulfilled_orders(order_id):
    path = '/admin/api/2024-01/locations.json'
    headers = {
        'X-Shopify-Access-Token': get_access_token(),
    }
    response = requests.get(
        HOST_SB + path,
        headers=headers,
    )

    create_shopify_log(method='get_locations',message=str(response.json()))

    # get_fulfillment_orders(order_id)
    path = '/admin/api/2024-01/orders/{}.json'.format(order_id)
    headers = {
        'X-Shopify-Access-Token': get_access_token(),
    }
    params = {
        # 'status': 'unfulfilled',
        'order_id' : order_id,
    }
    response = requests.get(
        HOST_SB + path,
        headers=headers,
    )

    create_shopify_log(method='get_spec',message=str(response.json()))

def get_access_token():
    shopify = frappe.get_single("Shopify Setting")
    pw = shopify.get_password('password')
    # create_shopify_log(message=pw)
    return pw

