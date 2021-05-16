# docker-redis

This repo will setup a simple redis counter with a custom docker bridge network.
We will look at three examples.

**docker examples**
[1] Flask and Redis - [Ref1](https://medium.com/@schogini/two-docker-container-communication-using-python-and-redis-a-tiny-demonstration-b9d7cd35daab)
[2] Flask and Redis with gunicorn [Ref2](https://github.com/alexryabtsev/docker-workshop)

**docker-compose example**
[3] Flask and Redis with gunicorn and nginx, use docker-compose [Ref3](https://github.com/OrangeTux/minimal-docker-python-setup)

[Optional] Replace gunicorn with uwsgi


We will start with below structure.
```
docker-redis
├── Dockerfile
├── app.py
└── requirements.tx
```
In the end you will get below structure.
```
docker-redis
├── Dockerfile
├── app.py
├── docker-compose.yml
├── nginx
│   ├── Dockerfile
│   └── nginx.conf
└── requirements.txt
```

## [1] Flask and Redis


### 1. Setup files

a) Flask app - create app.py inside web and add the following python code
```
import os
import socket

from flask import Flask
from redis import Redis


app = Flask(__name__)
redis = Redis(host="redis-server", db=0, socket_connect_timeout=2, socket_timeout=2)

@app.route('/')
def hello():
    redis.incr('hits')
    total_hits = redis.get('hits').decode()
    return f'Hello from Redis! I have been seen {total_hits} times.'


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=80)
```

b) Requirements file
```
flask==1.0.2
redis==2.10.6
```

c) Dockerfile - exposing the port 80
```
FROM python:3.6.3
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
COPY ./app.py /app.py
EXPOSE 80
CMD [ "python", "/app.py" ]
```


### 2. Create a custom bridge network 

`docker network create mynet`



### 3. Launch the Redis Server in the above network as “redis-server”.

`docker run -d --rm --name redis-server --network mynet redis:alpine`



### 4. Build and run our Python application in the root folder.

`docker build -t temp .`



### 5. Run the Docker Container

`docker run -d -p 8080:80 --rm --name pyapp --network mynet temp`

### 6. Test with curl
```
curl localhost:8080
Hello from Redis! I have been seen 9 times.
```

### 7. Stop just the temp container
```
docker ps
docker stop <containerID>
```

## [2] Flask and Redis with gunicorn run with docker-compose
```
client <-> gunicorn <-> Flask
```
### Carry on from above step 7.

### 8. Adding Gunicorn - with the port 8000
a) Change Dockerfile
```
#EXPOSE 80
#CMD [ "python", "/app.py" ]
CMD ["/usr/local/bin/gunicorn", "--workers=2", "-b 0.0.0.0:8000","app:app"]
```
b) Add requirements.txt
```
gunicorn==19.9.0
```
c) remove port 80 in app.py
```
app.run(host="0.0.0.0", debug=True)
```

### 8. Build our Python application in the root folder.

`docker build -t temp .`

### 9. Run the Docker Container

`docker run -d -p 8080:8000 --rm --name pyapp --network mynet temp`

### 10. Test with curl
```
curl localhost:8080
Hello from Redis! I have been seen 9 times.
```

### 11. Clean up 
Stop and remove the temp containers and the custom network created.
```
docker ps
docker stop <containerID for temp and redis-server>
docker images
docker rmi <app image>
docker network rm mynet
```
## [3] Flask and Redis with gunicorn and nginx
```
client <-> Nginx <-> gunicorn <-> Flask
```

### Carry on from above step 11.

### 12. Create a docker-compose file and add Nginx Dockerfile and nginx.conf
```
docker-redis
├── Dockerfile
├── app.py
├── docker-compose.yml
├── nginx
│   ├── Dockerfile
│   └── nginx.conf
└── requirements.txt
```
a) Create a docker-compose.yml
```
version: '3.7' 
services: 
  app: 
    build: 
      context: .
      dockerfile: Dockerfile 
    image: app 
    container_name: app 
    command: gunicorn --bind 0.0.0.0:8000 "app:app"
    expose: 
      - 8000 
    depends_on: 
      - redis-server
  nginx: 
    build: ./nginx 
    image: nginx 
    container_name: nginx 
    ports: 
      - 8000:80 
    depends_on: 
      - app 
  redis-server: 
    image: redis:alpine
    container_name: redis-server
```

b) Create Nginx Dockerfile

```
FROM nginx:1.17-alpine 
RUN rm /etc/nginx/conf.d/default.conf 
COPY nginx.conf /etc/nginx/conf.d 
```

c) Add nginx.conf

```
server { 
    listen 80; 
    location / { 
        proxy_pass http://app:8000; 
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; 
        proxy_set_header Host $host; 
        proxy_redirect off; 
    } 
}
```
d) Comment out Dockerfile
```
#CMD ["/usr/local/bin/gunicorn", "--workers=2", "-b 0.0.0.0:8000","app:app"]
```

### 13. Build our Python application in the root folder using docker-compose.

Note: you can replace `docker-compose` with `docker compose` - Docker Compose is now in the Docker CLI.

`docker-compose -f docker-compose.yml build`

### 14. Run the Docker Containers with docker-compose.

`docker-compose -f docker-compose.yml up -d`


### 15. Test with curl
```
curl localhost:8000
Hello from Redis! I have been seen 1 times.
```

### 16. Clean up 
Stop all containers and network with docker-compose, verify with `ps`
```
docker-compose -f docker-compose.yml down
docker ps
docker images
docker rmi <app, redis, nginx images>
```


## [Optional] Replace gunicorn with uwsgi


a) Configure uWSGI - In the same directory, create a file app.ini with:
```
[uwsgi]
protocol = uwsgi
; This is the name of our Python file
; minus the file extension
module = app
; This is the name of the variable
; in our script that will be called
callable = app
master = true
; Set uWSGI to start up 5 workers
processes = 5
; We use the port 5000 which we will
; then expose on our Dockerfile
socket = 0.0.0.0:5000
vacuum = true
die-on-term = true
```

b) replace gunicorn with below in requirements.txt
```
uwsgi==2.0.18
```
c) add below in Dockerfile
```
ENTRYPOINT ["uwsgi", "--http", "0.0.0.0:5000", "--module", "app:app", "--processes", "1", "--threads", "N"]
```