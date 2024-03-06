# from lazop_sdk_python.python.lazop import LazopClient, LazopRequest 
# from lazop import LazopClient, LazopRequest 
from lazop_sdk import LazopClient, LazopRequest 

def lazada_product_push():
    ### Lazada API Variables
    url = "https://api.lazada.com.my/rest"
    # url = "https://api.lazada.com.ph/rest"
    appkey = 126275
    appSecret = "7IrbxBBHReeC3DaApuBX13dFtu4BZtjT"
    access_token = "50000000809dxahr8Howz1cbd4c8ctphhcfTjivfvplXbBPgkzwjFmSHzdXHPGcC"

    client = LazopClient(url, appkey ,appSecret)

    # request = LazopRequest('/category/tree/get','GET')
    # request.add_api_param('language_code', 'en_US')

    request = LazopRequest('/product/item/get','GET')
    request.add_api_param('seller_sku', 'SKU LAZ1001')

    # request = LazopRequest('/auth/token/refresh')
    # request.add_api_param('refresh_token', '50001600212wcwiOabwyjtEH11acc19aBOvQr9ZYkYDlr987D8BB88LIB8bj')
    # response = client.execute(request)

    # request = LazopRequest('/auth/token/create')
    # request.add_api_param('code', '0_100132_2DL4DV3jcU1UOT7WGI1A4rY91')


    response = client.execute(request, access_token)
    print(response.type)
    print(response.body)
    # good Frappe inspiration
    # https://github.com/erpnext-apps/lazada_erpnext_connector/blob/a99b22723083143adec4fe2eb0ff4299b9209046/lazada_erpnext_connector/lazada_erpnext_connector/sales_order.py#L3

# lazada_product_push()

def sign(secret,api, parameters):
    #===========================================================================
    # @param secret
    # @param parameters
    #===========================================================================
    sort_dict = sorted(parameters)
    
    parameters_str = "%s%s" % (api,
        str().join('%s%s' % (key, parameters[key]) for key in sort_dict))

    h = hmac.new(secret.encode(encoding="utf-8"), parameters_str.encode(encoding="utf-8"), digestmod=hashlib.sha256)

    return h.hexdigest().upper()
