This is the basic _ITU_MiniTwit_ application (Python 3 and SQLite) with added support for logging with the ELF stack. The application is Dockerized.

_NOTICE:_ _The current setup is inspired by work done by [deviantony/docker-elk](https://github.com/deviantony/docker-elk). For more information and tips and tricks check out their repository._ (There is a TLS version found in that repository as well.)

### How to start the application

- Before running the stack (ELFK) is recommended to change the variables specified in the .env file.

- Before running the application use the following command to setup the correct environment.

```console
$ docker compose up setup
```

- This will leave the setup container with the status of exited. (see `docker ps -a`) To remove the setup container run

```console
$ docker compose down setup
```

- When the setup is done you can start the stack with the following command.

```console
$ docker compose up -d
```

_NOTE:_ _Be careful of not pushing your .env to github, if it contains confidential information_

After running `docker compose up`, 6 images should be up and running:

```
$ docker ps --format "table {{.Image}}\t{{.Names}}\t{{.Ports}}"
IMAGE                                 NAMES                                   PORTS
itu-minitwit-logging-minitwitclient   itu-minitwit-logging-minitwitclient-1   5000/tcp
itu-minitwit-logging-minitwitserver   minitwit                                0.0.0.0:5001->5000/tcp
itu-minitwit-logging-filebeat         itu-minitwit-logging-filebeat-1
itu-minitwit-logging-kibana           itu-minitwit-logging-kibana-1           0.0.0.0:5601->5601/tcp
itu-minitwit-logging-logstash         itu-minitwit-logging-logstash-1         0.0.0.0:5044->5044/tcp, 9600/tcp
itu-minitwit-logging-elasticsearch    itu-minitwit-logging-elasticsearch-1    0.0.0.0:9200->9200/tcp, 9300/tcp
```

### How to access parts of the application

- _ITU-MiniTwit_ at http://localhost:5001
- _ITU-MiniTwit Kibana Dasboard_ at http://localhost:5601, requiring the password defined in the .env file and the username elastic.
  _Use this user to create less privileged ones see: [built-in-user-passwords](https://www.elastic.co/guide/en/elasticsearch/reference/current/built-in-users.html#set-built-in-user-passwords) for more information_

### How to stop the application

To stop the application again run:

```bash
$ docker compose down -v
```

_Note:_ _The -v is stands for volumes, and will remove all named volumes specified in the docker compose. In this case it will delete the elasticsearch volume with all the saved data._

### Basics of how to use Kibana
1. Go to the Kibana Web UI at `http://localhost:5601/`, and login with the username `elastic` and the ELASTIC_PASSWORD defined in the .env file. 
2. Kibana has many ways to view the log data. Start by going to `Discover`, under the Analytics tab from the sidebar. This will prompt you to make a data view. 
3. Create a new data view. You should see the `logs-generic-default` Data stream which is the logs sent by logstash. 
4. The index pattern specifies what data the view should use. Set the index pattern to `logs-generic-default`, give it a name and save the data view to Kibana. 
5. In the discover view you should see logs being received in the graph, and you can edit the time you want to see in the top right. You can expand documents to view all the info from that log. In the list of available fields you can find things like `path` and `response code` which logstash parsed. 
6. Explore the `Dashboard` tab, also under the Analytics, where you can fx drag in the path field path, and get a graph of the most used endpoints
7. Check out `Stack Monitoring` at the bottom of the side panel to see the statistics of the filebeat instance. 
8. Lastly to manage users, data views and more, go to the last option in the side panel `Stack management`


### Breakdown of the configuration

Let's look at the docker-compose.yml present in our main directory:

```yaml
services:
  minitwitserver:
    restart: unless-stopped
    container_name: minitwit
    build:
      context: minitwit
    ports:
      - "5001:5000"
    networks:
      - main
    logging:
      driver: json-file

  minitwitclient:
    restart: unless-stopped
    build:
      context: minitwit_client
    networks:
      - main
    depends_on:
      - minitwitserver

  setup: ...

  elasticsearch:
    build:
      context: elasticsearch/
      args:
        ELASTIC_VERSION: ${ELASTIC_VERSION}
    volumes:
      - ./elasticsearch/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro,Z
      - elasticsearch:/usr/share/elasticsearch/data:Z
    ports:
      - 9200:9200 # Main Elasticsearch input
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
      - 5044:5044 # Beats input
    environment:
      LS_JAVA_OPTS: -Xms256m -Xmx256m
      LOGSTASH_INTERNAL_PASSWORD: ${LOGSTASH_INTERNAL_PASSWORD:-}
    networks:
      - elk
    depends_on:
      - elasticsearch
    restart: unless-stopped

  filebeat: # Uses another docker compose file to setup filebeat.
    extends:
      file: ./filebeat/filebeat-compose.yml
      service: filebeat

  kibana:
    build:
      context: kibana/
      args:
        ELASTIC_VERSION: ${ELASTIC_VERSION}
    volumes:
      - ./kibana/config/kibana.yml:/usr/share/kibana/config/kibana.yml:ro,Z
    ports:
      - 5601:5601 # Kibana UI Dashboard
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

- `minitwitserver` listening on port 5000 inside of the container (and 5001 on the host machine)
- `minitwitclient` running in the same `main` network and depending on our server
- `kibana`,`logstash` ,`filebeat` and `elasticsearch`, all within `elk` network.

Log pipeline:

1. Filebeat reads filebeat.yml and will automatically collect docker logs, with filebeat.autodiscover, from containers json.log files. Filebeat sends the log data to `logstash:5044`.
2. Logstash reads `pipeline/logstash.conf` and listens on port 5044 for filebeat data. Logstash uses a filter expression to get data fields from the logs, and sends the parsed logs to `elasticsearch:9200`.
3. Elastic search listens on port 9200 and gets the logstash data, as a data stream which it calls `logs-generic-default`. Creating a data-view on `logs-generic-default` you can see the extra fields extracted by logstash, if the log is a request to the server.

If for some reason you can't recreate using the `docker compose up setup` try `docker compose up setup --force-recreate` instead.
