This is the basic _ITU_MiniTwit_ application (Python 3 and SQLite) with added support for logging with the ELF stack. The application is Dockerized. 

### How to start the application
  * Setup some pre-required ENV variables and other stuff:
    ```bash
    sudo chmod +x setup_elk.sh
    source setup_elk.sh
    ```

  * Generate an authentication file for ngix proxy configuration:
    ```bash
    sudo apt-get install apache2-utils
    sudo htpasswd -c .htpasswd <USERNAME>
    ```
    **OR**
    ```bash
    printf "USERNAME:$(openssl passwd -crypt PASSWORD)\n" > .htpasswd
    ```
    Doesn't really matter which option you choose, as long as it results in you having a `.htpasswd` file in your main directory. The first option just avoids having your password in the console in plaintext.

  * Build the application:
    ```bash
    $ docker build -f docker/minitwit/Dockerfile -t $ELK_USER/webserver .
    ```

  * Build the test client:
    ```bash
    $ docker build -f docker/minitwit_client/Dockerfile -t $ELK_USER/minitwitclient .
    ```

  * Start the application:
    ```bash
    $ docker-compose up
    ```

    Alternatively, you can build and run the application in one step. Runing the following:
    
    ```bash
    $ docker-compose up --build
    ```

After running `docker-compose up`, 6 images should be up and running:
```
$ docker ps --format "table {{.Image}}\t{{.Names}}\t{{.Ports}}"
IMAGE                                                 NAMES                                   PORTS
tschesky/minitwitclient                               itu-minitwit-logging_minitwitclient_1   5000/tcp
nginx                                                 itu-minitwit-logging_nginx_1            0.0.0.0:5601->5601/tcp, 0.0.0.0:8881-8882->8881-8882/tcp, 80/tcp, 0.0.0.0:9200->9200/tcp
docker.elastic.co/elasticsearch/elasticsearch:7.2.0   itu-minitwit-logging_elasticsearch_1    9200/tcp, 9300/tcp
docker.elastic.co/beats/filebeat:7.2.0                itu-minitwit-logging_filebeat_1         
tschesky/minitwitserver                               minitwit                                0.0.0.0:5000->5000/tcp
docker.elastic.co/kibana/kibana:7.2.0                 itu-minitwit-logging_kibana_1           5601/tcp
```

### How to access parts of the application
  * _ITU-MiniTwit_ at http://localhost:5000
  * _ITU-MiniTwit Kibana Dasboard_ at http://localhost:5601, requiring atuhententication with previously defined username and password.


### How to stop the application
To stop the application again run:

```bash
$ docker-compose down -v
```

### Breakdown of the configuration
Let's look at the docker-compose.yml present in our main directory:
```yaml
version: '3.5'

networks:
  elk:
  main:
    name: itu-minitwit-network

volumes:
    elk_elasticsearch_data:

services:
  minitwitserver:
    build:
      context: .
      dockerfile: docker/minitwit/Dockerfile
    image: tschesky/minitwitserver
    container_name: minitwit
    ports:
      - "5000:5000"
    networks:
      - main

  minitwitclient:
    build:
      context: .
      dockerfile: docker/minitwit_client/Dockerfile
    image: tschesky/minitwitclient
    networks:
      - main
    depends_on:
      - minitwitserver

  elasticsearch:
    image: "docker.elastic.co/elasticsearch/elasticsearch:7.2.0"
    environment:
        - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
        - "discovery.type=single-node"
    volumes:
        - elk_elasticsearch_data:/usr/share/elasticsearch/data
    networks:
        - elk

  kibana:
    image: "docker.elastic.co/kibana/kibana:7.2.0"
    environment:
        elasticsearch.hosts: '["http://elasticsearch:9200"]'
    networks:
        - elk

  filebeat:
    image: "docker.elastic.co/beats/filebeat:7.2.0"
    user: root
    volumes:
        - ${ELK_DIR}/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
        - /var/lib/docker:/var/lib/docker:ro
        - /var/run/docker.sock:/var/run/docker.sock
    networks:
        - elk
          
  nginx: 
    image: nginx
    ports:
      - 9200:9200
      - 5601:5601
      - 8881:8881
      - 8882:8882
    networks:
      - elk
    volumes:
      - type: bind
        source: ${ELK_DIR}/nginx.conf
        target: /etc/nginx/nginx.conf
      - type: bind
        source: ${ELK_DIR}/.htpasswd
        target: /etc/nginx/.htpasswd
```

We have:
  * `minitwitserver` listening on port 5000
  * `minitwitclient` running in the same `main` network and depending on our server
  * `kibana`, `filebeat` and `elasticsearch`, all within `elk` network and not exposing any ports directly
  * Finally, we have `ngix` running in the same network and using our `ngix.conf` file to setup a proxy to elasticsearch

**Log indices**
We have configured Filebeat to use different indices for different containers, so we can more easily manage them in Kibana:

```yaml
indices:
    - index: "filebeat-elastic-%{[agent.version]}-%{+yyyy.MM.dd}"
      when.or:
        - equals:
            container.image.name: docker.elastic.co/beats/filebeat:7.2.0
        - equals:
            container.image.name: docker.elastic.co/elasticsearch/elasticsearch:7.2.0
        - equals:
            container.image.name: docker.elastic.co/kibana/kibana:7.2.0
    - index: "filebeat-minitwit-%{[agent.version]}-%{+yyyy.MM.dd}"
      when.or:
          - equals:
              container.image.name: ${ELK_USER}/minitwitserver
          - equals:
              container.image.name: ${ELK_USER}/minitwitclient
    - index: "filebeat-ngix-%{[agent.version]}-%{+yyyy.MM.dd}"
      when.equals:
        container.image.name: nginx
```

In your Kibana app use the following:
  * `filebeat-elastic-*` for kibana/elasticsearch logs
  * `filebeat-minitwit-*` for all of your Minitwit looging. You can also additionally split the logs between client/server
  * `filebeat-ngix-*` for logs from proxy, there is a lot of them, so we probably want them filtered out


**Proxy setup:**
```conf
http {
  upstream elasticsearch_up {
    server *elasticsearch*:9200;
  }

  upstream kibana_up {
    server *kibana*:5601;
  }

  server {
    listen 8881;
    location / {
      auth_basic "Restricted Access";
      auth_basic_user_file /etc/nginx/.htpasswd;
      proxy_pass "http://elasticsearch_up";
      ...
    }
  }
  server {
    listen 8882;
    location / {
      auth_basic "Restricted Access";
      auth_basic_user_file /etc/nginx/.htpasswd;
      proxy_pass "http://kibana_up";
      ...
    }
  }
}
```
  * Upstreams for our apps are both defined using container names that we have previously defined in our `docker-compose` and using default ports for both applications.
  * Then we listen on ports `8881/8882`, redirecting them to appropriate applications, but first requiring authentication, using the file originally created in setup for this exercise.

You can also enable the `xpack.security` module instead of using nginx, see https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html for details. This involves a bit more work, but improves your setups security by a lot.
