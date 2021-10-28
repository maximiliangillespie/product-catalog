'''
A GENERAL NOTE TO ANY INTERESTED READER:

this code is currently pretty rought around the edges. it's designed to demo some of the functionality of 
redis as more than a cache in its implementation of a simple product catalogue. 

it's pretty brittle at the moment – I've got quite a few todos laying around to tighten up error handling etc.
'''

import redis
from flask import Flask
from flask import request

client = redis.Redis(host = 'localhost', port = '6379', charset="utf-8", decode_responses=True)
app = Flask(__name__)

# keys for indexing db
productKey = "prd:"
productsKey = "prds:"
productNameSearchKey = "prd:srch"
imagesKey = "imgs:"
imagekey = "img:"
categoryKey = "cat:"
categoriesKey = "cats:"

'''
TODO:
    - make server source of truth for new product key gen
    - store actual binary rather than string
'''

'''
REQUIREMENTS:
    - Ability to delete product
'''

# EXTERNAL ROUTES ===================================================

@app.route("/product", methods=["POST"])
def API_CREATE_PRODUCT():
    product = request.get_json()
    # TODO: ERROR HANDLING
    create_new_product(product)
    create_images(product['id'], product['images'])
    create_new_category(product['id'], product['mainCategory'])
    return str(product['id'])

@app.route("/product/<product_id>", methods=["PUT"])
def API_UPDATE_PRODUCT(product_id):
    product = request.get_json()
    # TODO: ERROR HANDLING
    update_product(product, product_id)
    create_images(product_id, product['images'])
    update_category(product_id, product['mainCategory'])
    # TODO: update search key in search dict
    return "200"

@app.route("/product/<product_id>", methods=["DELETE"])
def API_DELETE_PRODUCT(product_id):
    # TODO: ERROR HANDLING
    # step 1: extract mainCategory & images
    # step 2: delete root product
    # step 3: extract products table from category
    # step 4: remove product id from 'prds:cat:n'
    # step 5: grab all keys from image set & delete keys associated with those images
    # step 6: delete images key 
    return product_id

@app.route("/product/<product_id>", methods=["GET"])
def API_FIND_PRODUCT_BY_ID(product_id):
    # TODO: ERROR HANDLING
    client_key = productKey + product_id
    all_keys = []
    product = {}
    for raw_prop in client.hgetall(client_key):
        product_prop = raw_prop
        product_val = client.hget(client_key, product_prop)
        if (product_prop == "images"):
            product_images = []
            product_images_keys = client.smembers(product_val)
            for product_image_key in product_images_keys:
                tmp_img = {}
                product_image_key_decoded = product_image_key
                for raw_image_prop in client.hgetall(product_image_key_decoded):
                    tmp_img[raw_image_prop] = client.hget(product_image_key_decoded, raw_image_prop)
                product_images.append(tmp_img)
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
    products_in_category = []
    for product_id in client.smembers(productsKey + categoryKey + category_id):
        products_in_category.append(API_FIND_PRODUCT_BY_ID(product_id))
    return str(products_in_category)

# takes string or substring search term
@app.route("/products/search")
def API_SEARCH_FOR_PRODUCT():
    search_term = request.args.get('search_term')
    return_items = []
    # TODO: ERROR HANDLING
    # TODO: grab potential product id's, return real JSON objects
    for search_result in client.hscan_iter(productNameSearchKey, search_term + "*"):
        return_items.append(API_FIND_PRODUCT_BY_ID(search_result[1]))
    return str(return_items)

# HELPER FUNCTIONS ===================================================

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
    # create product hash
    client_key = productKey + str(product_id)
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

# MAIN METHOD  ===================================================

app.run(debug = True)


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