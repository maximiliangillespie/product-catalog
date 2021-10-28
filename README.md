Product Catalog Use Case

In the last session several common Redis use cases were discussed. Now, let's consider using Redis as our primary data base for a product catalog for a new online store. It will need to store product details should including a name, description, vendor, price, main category and some images.

-----------------------

Requirements

- Product information stored in the database should include: name, description, vendor, price, category, images associated with that product
- Ability to create/update/delete product details
- Ability to find product by ID
- Ability to find products in category X
- Ability to find product by it's name or part of it's name

-----------------------

Logical Data Model

Product Image
- id: number
- Value : Binary

Product
- Id : Number
- Name : String
- Description: String
- Vendor : String
- Price : Number
- Currency : String
- MainCategory : Category (1)
- Images : Image (0..n)

Category
- Id : Number
- Name : String
- Products : Product (0..n)



