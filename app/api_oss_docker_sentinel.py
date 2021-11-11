'''
A GENERAL NOTE TO ANY INTERESTED READER:

this code is currently pretty rought around the edges. it's designed to demo some of the functionality of 
redis as more than a cache in its implementation of a simple product catalogue. 

it's pretty brittle at the moment – I've got quite a few todos laying around to tighten up error handling etc.
'''

from redis.sentinel import Sentinel
from redis import Redis
from flask import Flask
from flask import request

conf = {
    'sentinel': [('redis-sentinel-1', 26379), ('redis-sentinel-2', 26379), ('redis-sentinel-3', 26379)],
    'master_group_name': 'rmain',
    #Connect sentinel configuration
    'sentinel_conf': { 
        'socket_timeout': 3,
        'socket_keepalive': True,
    #    'password': 'w2opw723DaAp0rUc'
    },
    'connection_conf': {
        'socket_timeout': 3,
        'retry_on_timeout': True,
        'socket_keepalive': True,
        'max_connections': 5,
        'db': 0,
        #'password': 'w2opw723DaAp0rUc',
        'encoding': 'utf8'
    }
}

# keys for indexing db
productKey = "prd:"
productsKey = "prds:"
productNameSearchKey = "prd:srch"
imagesKey = "imgs:"
imagekey = "img:"
categoryKey = "cat:"
categoriesKey = "cats:"

# instantiate redis and sentinel instances
# r = Redis(host = '127.0.0.1', port=26379)  # <= for trying to do pubsub stuff
sentinel = Sentinel(conf['sentinel'],sentinel_kwargs=conf['sentinel_conf'],**conf['connection_conf'])
sentinel.discover_master(conf['master_group_name'])

client = sentinel.master_for(conf['master_group_name'])

app = Flask(__name__)

'''
TODO:
    - make server source of truth for new product key gen
    - make search case sensitive? 
'''

# EXTERNAL ROUTES ===================================================

@app.route("/product", methods=["POST"])
def API_CREATE_PRODUCT():
    # TODO: ERROR HANDLING
    discover_master()
    product = request.get_json()
    create_new_product(product)
    create_images(product['id'], product['images'])
    create_new_category(product['id'], product['mainCategory'])
    return str(product['id'])

@app.route("/product/<product_id>", methods=["PUT"])
def API_UPDATE_PRODUCT(product_id):
    # TODO: ERROR HANDLING
    discover_master()
    product = request.get_json()
    update_product(product, product_id)
    create_images(product_id, product['images'])
    update_category(product_id, product['mainCategory'])
    return str(product_id)

@app.route("/product/<product_id>", methods=["DELETE"])
def API_DELETE_PRODUCT(product_id):
    # TODO: ERROR HANDLING
    discover_master()
    client_key = productKey + product_id
    mainCategory_key = client.hget(client_key, 'mainCategory')
    images_key = client.hget(client_key, 'images')
    product_name = client.hget(client_key, 'name')
    # remove product from search table
    client.hdel(productNameSearchKey, product_name)
    # extract products table from category & remove product_id from 'prds:cat:n'
    category_products_key = client.hget(mainCategory_key, 'products')
    client.srem(category_products_key, product_id)
    if (client.scard(category_products_key) == 0):
        client.delete(mainCategory_key) # delete main category if there are no members left
    # grab all keys from image set & delete keys associated with those images
    for image_info_key in client.smembers(images_key):
        client.delete(image_info_key)
    # delete images key 
    client.delete(images_key)
     # delete root product
    client.delete(client_key)
    return product_id

@app.route("/product/<product_id>", methods=["GET"])
def API_FIND_PRODUCT_BY_ID(product_id):
    # TODO: ERROR HANDLING
    discover_master()
    client_key = productKey + product_id
    product = {}
    for product_prop in client.hgetall(client_key):
        product_val = client.hget(client_key, product_prop)
        if (product_prop == "images"):
            product_images = []
            for product_image_key in client.smembers(product_val):
                product_images.append(client.hgetall(product_image_key))
            product[product_prop] = product_images
        elif (product_prop == "mainCategory"):
            product_category = client.hgetall(product_val)
            del product_category['products'] # this is an internal tracking mechanism, don't return to user
            product[product_prop] = product_category
        else:
            product[product_prop] = product_val
    return product

# TODO: additional feature that could be cool would be ability to specify with a flag whether we just want product id, name, or full product object.
@app.route("/products/<category_id>")
def API_FIND_PRODUCTS_IN_CATEGORY(category_id):
    discover_master()
    products_in_category = []
    for product_id in client.smembers(productsKey + categoryKey + category_id):
        products_in_category.append(API_FIND_PRODUCT_BY_ID(product_id))
    return str(products_in_category)

# takes string or substring search term
@app.route("/products/search")
def API_SEARCH_FOR_PRODUCT():
    # TODO: ERROR HANDLING
    discover_master()
    search_term = request.args.get('search_term')
    return_items = []
    for search_result in client.hscan_iter(productNameSearchKey, search_term + "*"):
        return_items.append(API_FIND_PRODUCT_BY_ID(search_result[1]))
    return str(return_items)

# HELPER FUNCTIONS ===================================================

def discover_master():
    global client
    sentinel.discover_master(conf['master_group_name'])
    client = sentinel.master_for(conf['master_group_name'])

def create_new_product(product = {}):
    product_id = product['id']
    category_id = product['mainCategory']['id']
    # create product hash
    client_key = productKey + str(product_id)
    for product_prop in product.keys():
        if (product_prop == "images"):
            # need special case for this. we pass in a list of images but want to provide a ref to the image list instead
            client.hsetnx(client_key, product_prop, imagesKey + str(product_id))
        elif (product_prop == "mainCategory"):
            client.hsetnx(client_key, product_prop, categoryKey + str(product[product_prop]['id']))
        else:
            client.hsetnx(client_key, product_prop, product[product_prop])
    # add product to products table for its category
    products_key = productsKey + categoryKey + str(category_id)
    client.sadd(products_key, product_id)
    client.hset(productNameSearchKey, product['name'], product_id)

def update_product(product = {}, product_id = -1):
    category_id = product['mainCategory']['id']
    client_key = productKey + str(product_id)
    #update product search key
    client.hdel(productNameSearchKey, client.hget(client_key, 'name'))
    client.hset(productNameSearchKey, product['name'], product_id)
    # create product hash
    for product_prop in product.keys():
        if (product_prop == "images"):
            # need special case for this. we pass in a list of images but want to provide a ref to the image list instead
            client.hset(client_key, product_prop, imagesKey + str(product_id))
        elif (product_prop == "mainCategory"):
            client.hset(client_key, product_prop, categoryKey + str(product[product_prop]['id']))
        else:
            client.hset(client_key, product_prop, product[product_prop])
    # add product to products table for its category
    products_key = productsKey + categoryKey + str(category_id)
    client.sadd(products_key, product_id)

def create_images(product_id = -1, images = []):
    images_key = imagesKey + str(product_id)
    for image in images:
        image_key = productKey + str(product_id) + ":" + imagesKey + image['id']
        client.sadd(images_key, image_key)
        for image_prop in image:
            client.hset(image_key, image_prop, image[image_prop])

def create_new_category(product_id = -1, category = {}):
    category_id = category['id']
    category_key = categoryKey + str(category_id)
    for category_prop in category.keys():
        client.hsetnx(category_key, category_prop, category[category_prop])
    products_key = productsKey + categoryKey + str(category['id'])
    client.hsetnx(category_key, 'products', products_key)
    client.sadd(products_key, product_id)

def update_category(product_id = -1, category = {}):
    category_id = category['id']
    category_key = categoryKey + str(category_id)
    for category_prop in category.keys():
        client.hset(category_key, category_prop, category[category_prop])
    products_key = productsKey + categoryKey + str(category['id'])
    client.hset(category_key, 'products', products_key)
    client.sadd(products_key, product_id)

# master failover handler (not yet figured out)
# def handle_switch_master():
#     print('MASTER SWITCHED')

# MAIN METHOD  ===================================================

# listen to pubsub for master failover (haven't figured this out yet)
# pubsub = r.pubsub()
# pubsub.subscribe('+switch-master', handle_switch_master)

app.run(host='0.0.0.0', debug = True)

# TESTING  ===================================================

# product = {
#     "id": 1000,
#     "name": "name",
#     "description": "some description",
#     "vendor": "vendor name",
#     "price": 33,
#     "currency": "ETH",
#     "mainCategory": {
#         "id": 1,
#         "name": "category name"
#     },
#     "images": [
#         {
#             "id": "img_1_src",
#             "val": "01101011"
#         }, {
#             "id": "img_2_src",
#             "val": "01101011"
#         }
#     ]
# }

# API_CREATE_PRODUCT(product)