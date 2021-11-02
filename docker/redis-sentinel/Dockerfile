FROM redis:6.2-alpine
 
RUN mkdir -p /redis
 
WORKDIR /redis
 
COPY sentinel.conf .
COPY docker-entrypoint.sh /usr/local/bin/
 
RUN chown redis:redis /redis/* && \
    chmod +x /usr/local/bin/docker-entrypoint.sh
 
EXPOSE 26379
EXPOSE 5000
 
ENTRYPOINT ["docker-entrypoint.sh"]