#!/bin/sh

sed -i "s/_MAIN_HOST/$MAIN_HOST/g" /redis/sentinel.conf
sed -i "s/_SENTINEL_QUORUM/$SENTINEL_QUORUM/g" /redis/sentinel.conf
sed -i "s/_SENTINEL_DOWN_AFTER/$SENTINEL_DOWN_AFTER/g" /redis/sentinel.conf
sed -i "s/_SENTINEL_FAILOVER/$SENTINEL_FAILOVER/g" /redis/sentinel.conf
 
redis-server /redis/sentinel.conf --sentinel