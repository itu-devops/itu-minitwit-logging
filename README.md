This is the basic _ITU_MiniTwit_ application (Python 3 and SQLite) with added support for logging with the ELF stack. The application is Dockerized. 

There's an alternative branch that uses the EFK 8 stack with nginx at [EFK 8](https://github.com/itu-devops/itu-minitwit-logging/tree/efk-8) stack (instead of EFK 7), but note that we were unable to make it work on all of our machines. See the [diff](https://github.com/itu-devops/itu-minitwit-logging/commit/2d814fb3b216b2a6ab3d769f4915e7f5c371c52f) for changes.


*NOTICE:* _The current setup is inspired by work done by [deviantony/docker-elk](https://github.com/deviantony/docker-elk). For more information and tips and tricks check out their repository._

### How to start the application
  * Before running the stack (ELFK) is recommended to change the variables specified in the .env file.

  * Before running the application use the following command to setup the correct environment.
  ```console
  $ docker compose up setup
  ```

  * When it is done you can start the stack with the following command.
  ```console
  $ docker compose up -d
  ```

*NOTE:* _Be careful of not pushing your .env to github, if it contains confidential information_

After running `docker-compose up`, 6 images should be up and running:
```
$ docker ps --format "table {{.Image}}\t{{.Names}}\t{{.Ports}}"
IMAGE                              NAMES                         PORTS
docker-elk-minitwitclient          docker-elk-minitwitclient-1   5000/tcp
docker-elk-filebeat                docker-elk-filebeat-1         
docker-elk-logstash                docker-elk-logstash-1         0.0.0.0:5044->5044/tcp, :::5044->5044/tcp, 0.0.0.0:9600->9600/tcp, :::9600->9600/tcp, 0.0.0.0:50000->50000/tcp, :::50000->50000/tcp, 0.0.0.0:50000->50000/udp, :::50000->50000/udp
docker-elk-kibana                  docker-elk-kibana-1           0.0.0.0:5601->5601/tcp, :::5601->5601/tcp
docker-elk-minitwitserver          minitwit                      0.0.0.0:5000->5000/tcp, :::5000->5000/tcp
docker-elk-elasticsearch           docker-elk-elasticsearch-1    0.0.0.0:9200->9200/tcp, :::9200->9200/tcp, 0.0.0.0:9300->9300/tcp, :::9300->9300/tcp
```

### How to access parts of the application
  * _ITU-MiniTwit_ at http://localhost:5000
  * _ITU-MiniTwit Kibana Dasboard_ at http://localhost:5601, requiring authentication username and password defined in the .env file.


### How to stop the application
To stop the application again run:

```bash
$ docker-compose down -v
```

### Breakdown of the configuration
Let's look at the docker-compose.yml present in our main directory:
```yaml
version: '3.7'

services:
  minitwitserver:
    restart: unless-stopped
    container_name: minitwit
    build:
      context: .
      dockerfile: docker/minitwit/Dockerfile
    ports:
      - "5000:5000"
    networks:
      - main

  minitwitclient:
    restart: unless-stopped
    build:
      context: .
      dockerfile: docker/minitwit_client/Dockerfile
    networks:
      - main
    depends_on:
      - minitwitserver

  setup:
    ...

  elasticsearch:
    build:
      context: elasticsearch/
      args:
        ELASTIC_VERSION: ${ELASTIC_VERSION}
    volumes:
      - ./elasticsearch/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro,Z
      - elasticsearch:/usr/share/elasticsearch/data:Z
    ports:
      - 9200:9200
      - 9300:9300
    environment:
      node.name: elasticsearch
      ES_JAVA_OPTS: -Xms512m -Xmx512m
      ELASTIC_PASSWORD: ${ELASTIC_PASSWORD:-}
      discovery.type: single-node
    networks:
      - elk
    restart: unless-stopped

  logstash:
    build:
      context: logstash/
      args:
        ELASTIC_VERSION: ${ELASTIC_VERSION}
    volumes:
      - ./logstash/config/logstash.yml:/usr/share/logstash/config/logstash.yml:ro,Z
      - ./logstash/pipeline:/usr/share/logstash/pipeline:ro,Z
    ports:
      - 5044:5044
      - 50000:50000/tcp
      - 50000:50000/udp
      - 9600:9600
    environment:
      LS_JAVA_OPTS: -Xms256m -Xmx256m
      LOGSTASH_INTERNAL_PASSWORD: ${LOGSTASH_INTERNAL_PASSWORD:-}
    networks:
      - elk
    depends_on:
      - elasticsearch
    restart: unless-stopped

  filebeat: # Uses another docker compose file to setup filebeat. Use this trick to enable other extensions if you want to.
    extends:
      file: ./extensions/filebeat/filebeat-compose.yml
      service: filebeat

  kibana:
    build:
      context: kibana/
      args:
        ELASTIC_VERSION: ${ELASTIC_VERSION}
    volumes:
      - ./kibana/config/kibana.yml:/usr/share/kibana/config/kibana.yml:ro,Z
    ports:
      - 5601:5601
    environment:
      KIBANA_SYSTEM_PASSWORD: ${KIBANA_SYSTEM_PASSWORD:-}
    networks:
      - elk
    depends_on:
      - elasticsearch
    restart: unless-stopped

networks:
  elk:
    driver: bridge
  main:


volumes:
  elasticsearch:

```

We have:
  * `minitwitserver` listening on port 5000
  * `minitwitclient` running in the same `main` network and depending on our server
  * `kibana`,`logstash` ,`filebeat` and `elasticsearch`, all within `elk` network and not exposing any ports directly

**Log indices**
We have configured Filebeat to use different indices for different containers, so we can more easily manage them in Kibana:

```yaml
  indices:
      - index: "filebeat-elastic-%{[agent.version]}-%{+yyyy.MM.dd}"
        when.or:
          - equals:
              container.image.name: docker-elk-filebeat
          - equals:
              container.image.name: docker-elk-elasticsearch
          - equals:
              container.image.name: docker-elk-kibana
      - index: "filebeat-minitwit-%{[agent.version]}-%{+yyyy.MM.dd}"
        when.or:
            - equals:
                container.image.name: docker-elk-minitwitserver
            - equals:
                container.image.name: docker-elk-minitwitclient
      - index: "filebeat-ngix-%{[agent.version]}-%{+yyyy.MM.dd}"
        when.equals:
          container.image.name: nginx
```

In your Kibana app use the following:
  * `filebeat-elastic-*` for kibana/elasticsearch logs
  * `filebeat-minitwit-*` for all of your Minitwit looging. You can also additionally split the logs between client/server
  * `filebeat-ngix-*` for logs from proxy, there is a lot of them, so we probably want them filtered out

If for some reason you can't recreate using the `docker compose up setup` try `docker compose up setup --force-recreate` instead. 