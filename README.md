# Event Bus Architecture Demo

## Developer

### Install RabbitMQ Locally

```bash
docker run -d --hostname rabbit --name rabbit-management -p 5672:5672 15672:15672 rabbitmq:3-management
```

Check that Rabbit MQ is running [http://localhost:15672/#/](http://localhost:15672/#/)

```bash
docker ps
```

Getting into RabbitMQ to config and go mad.

```bash
docker exec --interactive --tty rabbit-management bash
rabbitmqctl list_queues
```

### Test your python publisher script

```bash
pip install pika
pip install time
```

```python
#!/usr/bin/env python
import time
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='hello')

while (True):
    channel.basic_publish(exchange='',
                        routing_key='hello',
                        body='Hello World!')
    print(" [x] Sent 'Hello World!'")
    time.sleep(1)

connection.close()
```

```bash
chmod a+x publisher.py
/publisher.py
```

### Test you python subscriber script

```python
#!/usr/bin/env python
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='hello')

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)

channel.basic_consume(callback,
                    queue='hello',
                    no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
```

```bash
chmod a+x subscriber.py
./subscriber.py
```

### Build your docker and push to repository

```dockerfile
FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install pika

COPY . .

CMD [ "python", "./publisher.py" ]
```

```dockerfile
FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install pika

COPY . .

CMD [ "python", "./subscriber.py" ]
```

```bash
docker build --file Dockerfile-publisher --tag py-publisher .
docker build --file Dockerfile-subscriber --tag py-subscriber .
```

```bash
docker run -it --rm --name py-publisher py-publisher
docker run -it --rm --name py-subscriber py-subscriber
```

```bash
export DOCKER_ID_USER="username"
docker login
docker tag py-publisher $DOCKER_ID_USER/py-publisher
docker push $DOCKER_ID_USER/py-publisher
docker tag py-subscriber $DOCKER_ID_USER/py-subscriber
docker push $DOCKER_ID_USER/py-subscriber

```

## Operations

### Install Kubernetes Components

#### Install Virtual Machine Management

I use VirtualBox.

```bash
sudo apt install virtualbox virtualbox-ext-pack
```

#### Install Kubectl

Kubectl will be used to control your production and minikube clusters.

```bash
sudo apt update
sudo apt install -y apt-transport-https
sudo su
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb http://apt.kubernetes.io/ kubernetes-xenial main
EOF
exit
sudo apt update
sudo apt install -y kubectl
```

#### Install Minikube

To install minikube you can check the following link or use the short commands below for linux. [https://kubernetes.io/docs/tasks/tools/install-minikube/](https://kubernetes.io/docs/tasks/tools/install-minikube/)

```bash
curl -Lo minikube https://storage.googleapis.com/minikube/releases/v0.26.1/minikube-linux-amd64 && \
chmod +x minikube && \
sudo mv minikube /usr/local/bin/
```

Start and check whether your minikube cluster is up and running.

```bash
minikube start
minikube dashboard
```

Check that kubectl can connect and the cluster information.

```bash
kubectl config current-context
kubectl cluster-info
```

### Deploy RabbitMQ

```yaml
apiVersion: v1
kind: Service
metadata:
  labels:
    component: rabbitmq
  name: rabbitmq-service
spec:
  ports:
  - port: 5672
    name: rabbitmq
  - port: 15672
    name: management
  - port: 25672
    name: gossip
  selector:
    app: rabbitmq-pubsub
    component: rabbitmq
```

```yaml
apiVersion: v1
kind: ReplicationController
metadata:
  labels:
    component: rabbitmq
  name: rabbitmq-controller
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: rabbitmq-pubsub
        component: rabbitmq
    spec:
      containers:
      - image: rabbitmq:3-management
        name: rabbitmq
        ports:
        - containerPort: 5672
        - containerPort: 15672
        - containerPort: 25672
        resources:
          limits:
            cpu: 100m
```

#### Deploy to Minikube

```bash
kubectl create -f .
```

Check that Rabbit MQ is running [http://localhost:15672/#/](http://localhost:15672/#/)