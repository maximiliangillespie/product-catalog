import redis

client = redis.Redis(host='localhost', port='6379')

# redis keys for prefixing tables
productKey = "product:"
productsKey = "products:"
imagesKey = "images:"
imagekey = "image:"
categoryKey = "category:"
categoriesKey = "categories:"

# starting values
product_id = 1000
company_id = 2000
category_id = 3000
image_id = 4000

# SEED DB
# this is the process for adding one element fully to a table. 
# this element contains a list of images, an associated category, and a number of unique 

# step 1: product table
client_key = productKey + str(product_id)
product = {
    "id": product_id,
    "name": "name",
    "description": "some description",
    "vendor": "vendor name",
    "price": 33,
    "currency": "ETH",
    "mainCategory": category_id,
    "images": imagesKey + str(product_id)
}
for product_key in product.keys():
    client.hset(client_key, product_key, product[product_key])

# step 1.5: products table
products_key = productsKey + str(category_id)
client.sadd(products_key, product_id)

# step 2: images table
images_key = imagesKey + str(product_id)
num_images_to_add = 4
for i in range(0, num_images_to_add):
    client.sadd(images_key, str(image_id + i))

# step 3: image tables
image_key = imagekey + str(image_id)
for i in range(0, num_images_to_add):
    image_id += i
    image = {
        "id": image_id,
        "val": "binary" # TODO: go back here and make this binary
    }
    for key in image.keys():
        client.hset(image_key, key, image[key])

# step 4: category table
category_key = categoryKey + str(category_id)
category = {
    "id": category_id,
    "name": "category name",
    "products": productsKey + str(category_id)
}
for key in category.keys():
    client.hset(category_key, key, category[key])
