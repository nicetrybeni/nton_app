"""import requests
import frappe
import json


@frappe.whitelist(allow_guest=True)
def shopify_get_token():
    api_key = 'c9741db2a03b405a2ec4752ab733d270'
    api_secret = '88eaaf8b2b010fcad8186d08c9a280a3'
    admin_api_access_token = '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'
    scope = 'write_draft_orders, read_draft_orders, write_orders, read_orders, read_locations, read_customers, write_assigned_fulfillment_orders, read_assigned_fulfillment_orders, write_product_listings, read_product_listings, write_products, read_products, write_inventory, read_inventory, read_discounts, read_files, read_gift_cards, read_online_store_pages, write_order_edits, read_order_edits, write_shipping, read_shipping'
    redirect_url = 'https://admin.shopify.com/store/n2n-sandbox/oauth/callback' #test
    state = 'test' #test
    grant_option = 'per-user'

    authorization_code = frappe.request.args.get('code') # get authorization_code

    # if authorization_code is existing
    if authorization_code:
        # Exchange authorization code for access token
        url = f'https://admin.shopify.com/store/n2n-sandbox/admin/oauth/access_token'
        payload = {
            'client_id': api_key,
            'client_secret': api_secret,
            'code': authorization_code
        }
        response = requests.post(url, data=payload)

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data['access_token']
            refresh_token = token_data['refresh_token']

            shopify_cred = frappe.get_doc({
                'doctype': 'ShopifyCredentials',
                'access_token': access_token,
                'refresh_token': refresh_token
            })
            shopify_cred.insert()
            frappe.db.commit()

            return f'Access token stored'
        else:
            return f'Error exchanging authorization code for access token: {response.text}'
        
    # if there is no authorization_code yet, return authorization_url as redirect_url to access authorization_code
    else:
        authorization_url = f'https://admin.shopify.com/store/n2n-sandbox/admin/oauth/authorize?client_id={api_key}&scope={scope}&redirect_url={redirect_url}&state={state}&grant_option[]={grant_option}'
        
        return {
            "redirect_url": authorization_url
        }
"""