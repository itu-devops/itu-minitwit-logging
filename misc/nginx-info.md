
  * Generate an authentication file for nginx proxy configuration:
    ```bash
    sudo apt-get install apache2-utils
    sudo htpasswd -c .htpasswd <USERNAME>
    ```
    **OR**
    ```bash
    printf "USERNAME:$(openssl passwd -crypt PASSWORD)\n" > .htpasswd
    ```
    Doesn't really matter which option you choose, as long as it results in you having a `.htpasswd` file in your main directory. The first option just avoids having your password in the console in plaintext.


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
