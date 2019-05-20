# Docker and Kubernetes DevOps Demo

## Developer

### Install RabbitMQ Locally

```bash
docker run -d --hostname rabbit --name rabbit-management -p 5672:5672 -p 15672:15672 rabbitmq:3-management
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
import os
import time
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(localhost))
channel = connection.channel()
channel.exchange_declare(exchange='data',exchange_type='topic')
channel.queue_declare(queue='demo')
channel.queue_bind(queue='demo',exchange='data',routing_key='hello')

while (True):
    channel.basic_publish(exchange='data',
                        routing_key='hello',
                        body='Hello World!')
    print(" [x] Sent 'Hello World!'")
    time.sleep(1)

connection.close()
```

```bash
RABBITMQ_SERVER=localhost
chmod a+x publisher.py
/publisher.py
```

### Test you python subscriber script

```python
#!/usr/bin/env python
import os
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(localhost))
channel = connection.channel()
channel.queue_declare(queue='demo')

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)

channel.basic_consume('demo',
                    callback,
                    auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
```

```bash
RABBITMQ_SERVER=localhost
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

### Install AZ cli

```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

```bash
az login
az account list --subscription
az aks install-cli
```

### Install Kubernetes Components

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

### Install AKS Cluster

```bash
az group create -l westeurope -n aks-resource-group
az aks create -g aks-resource-group -n aks-cluster --kubernetes-version 1.12.6
```