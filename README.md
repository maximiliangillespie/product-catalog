# Product Catalog

A simple product catalog demonstrating the power of redis enterprise & some of the basic redis (oss and enterprise) functionalities

## Components
* app/api_enterprise.py: redis enterprise instance of product catalog
* app/api_oss_standalone.py: dockerized redis oss instance running 1 shard locally
* app/api_oss_docker_sentinel.py: dockerized sentinel instance of 

## Current Features

* product information stored in the database that includes: name, description, vendor, price, category, images associated with that product
* create/update/delete product details
* find product by id
* find products by category id
* find product by its name or part of its name

## Using

```
docker-compose up
```

### ...with a single shard

launch api locally:

```
python3 api_oss_standalone.py
```

You can now use postman to interact with the DB as you would normally with an API. View changes to the shard in 

**NOTE:** technically I'm just starding a sentinel instance in either case. I don't think this matters because for this demo my script just connects to the single shard as if it's a standalone instance. we lose the client-side benefits of rediscovering master, but besides that this can work with any standalone shard in whatever context you want to use it in.

In other words, if 

``` 
redis-cli
```

works on your local machine, you should be good to go with this approach

### ...with oss sentinel

#### start api

Launch api on docker network:

```
docker-compose exec app python usr/local/app/api_oss_docker_sentinel.py
```

You can now use postman to interact with the DB as you would normally with an API. Follow the instructions below to trigger a failover / demo a recovery.

#### interact with sentinel

In another terminal tab/window pause the redis-main container you can run sentinel commands to verify things are working.

**discover master**
```
docker-compose exec redis-sentinel-1 redis-cli -p 26379 sentinel master rmain
```

**discover sentinels**
```
docker-compose exec redis-sentinel-1 redis-cli -p 26379 sentinel sentinels rmain
```

**discover replicas**
```
docker-compose exec redis-sentinel-1 redis-cli -p 26379 sentinel replicas rmain
```

**failover**
```
docker-compose pause redis-main 
```

View the logs in the main docker-compose window/tab to see the failover occur.  Check the state via redis-cli...

```
docker-compose exec redis-sentinel-1 redis-cli -p 26379 sentinel master rmain
```

Recover the container

```
docker-compose unpause redis-main 
```

Sentinel instances should automatically detect that the master instance is reachable again. Check the state via redis-cli...

```
docker-compose exec redis-sentinel-1 redis-cli -p 26379 sentinel master rmain
```

## Logical Data Model

### Product Image
* id: number
* Value : Binary

### Product
* Id : Number
* Name : String
* Description: String
* Vendor : String
* Price : Number
* Currency : String
* MainCategory : Category (1)
* Images : Image (0..n)

### Category
* Id : Number
* Name : String
* Products : Product (0..n)

## Feature wishlist
* redisearch