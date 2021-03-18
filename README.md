This is the basic _ITU_MiniTwit_ application (Python 3 and SQLite) with added support for monitoring with Prometheus and Grafana as a Dashboard.

The application is Dockerized. To build the application and a client which simulates users clicking around the front page you have to:

  * Build the application:
```bash
$ docker build -f docker/minitwit/Dockerfile -t <youruser>/webserver .
```

  * Build the test client:
```bash
$ docker build -f docker/minitwit_client/Dockerfile -t <youruser>/minitwitclient .
```


  * Start the application:
```bash
$ docker-compose up
```

Alternatively, you can build and run the application in one step.
**OBS:** Remember to replace `<youruser>` in `docker-compose.yml` with your DockerHub user name before running the following:

```bash
$ docker-compose up --build
```


To stop the application again run:

```bash
$ docker-compose down -v
```

After starting the entire application, you can reach:

  * _ITU-MiniTwit_ at http://localhost:5000
  * _ITU-MiniTwit_ logs <TBD>


<TBD>