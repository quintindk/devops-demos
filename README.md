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
    targetPort: 35672
    name: rabbitmq
  - port: 36672
    targetPort: 15672
    name: management
  - port: 37672
    targetPort: 25672
    name: gossip
  selector:
    app: rabbitmq-pubsub
    component: rabbitmq
  type: NodePort
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

## Cloud

## Login and select subscription

```bash
az login

az account list -o table

az account set --subscription <someid>
```

## Resource Group

```bash
az group create --name acsresourcegroup --location westeurope
```

This will create the resource group for all the components for testing.

## Networking

### VNET ans Subnets

```bash
az network vnet create \
    --name k8s_vnet \
    --resource-group acsresourcegroup \
    --location westeurope \
    --address-prefix 10.1.0.0/20 \
    --subnet-name k8s_subnet \
    --subnet-prefix 10.1.0.0/20
```

## Azure Container Services (Kubernetes)

Here using the steps outlined in this line [https://github.com/Azure/acs-engine/blob/master/docs/kubernetes/deploy.md](https://github.com/Azure/acs-engine/blob/master/docs/kubernetes/deploy.md#acs-engine-the-long-way).

### SSH Keys

This is specific to Linux.

```bash
mkdir ~/.ssh
chmod 700 ~/.ssh
ssh-keygen -t rsa
```

### Service Principal

Here you need to be Global administrator AD permissions and Owner Azure resources (in the subscriptions) permissions. Check this article to configure your user for the correct roles [https://docs.microsoft.com/en-us/azure/azure-resource-manager/resource-group-create-service-principal-portal](https://docs.microsoft.com/en-us/azure/azure-resource-manager/resource-group-create-service-principal-portal). Once you have the right roles you can create the service principal.

```bash
az ad sp create-for-rbac --name azure_serviceprincipal --password <somepassword>
```

```json
{
  "appId": "<someappid>",
  "displayName": "azure_serviceprincipal",
  "name": "http://azure_serviceprincipal",
  "password": "<somepassword>",
  "tenant": "<sometenant>"
}
```

Confirm the service principal is correct.

```bash
az login --service-principal -u azure_serviceprincipal -p <somepassword> --tenant <sometenant>
az vm list-sizes --location westeurope
az logout
```

### Azure Acs Engine (acs-engine)

More info [https://github.com/Azure/acs-engine/blob/master/docs/kubernetes/deploy.md](https://github.com/Azure/acs-engine/blob/master/docs/kubernetes/deploy.md)

Edit the kubernetes.json file to add everything that's necessary.

```json
{
  "apiVersion": "vlabs",
  "properties": {
    "orchestratorProfile": {
      "orchestratorType": "Kubernetes",
      "orchestratorVersion": "1.9.1",
      "kubernetesConfig": {
        "networkPolicy": "none"
      }
    },
    "masterProfile": {
      "count": 1,
      "dnsPrefix": "k8s_test",
      "vmSize": "Standard_D2_v2",
      "distro" : "coreos",
      "vnetSubnetId": "/subscriptions/<somesubsid>/resourceGroups/acsresourcegroup/providers/Microsoft.Network/virtualNetworks/k8s_vnet/subnets/k8s_subnet",
      "firstConsecutiveStaticIP": "10.243.2.7",
      "vnetCidr": "10.243.2.0/24"
    },
    "agentPoolProfiles": [
      {
        "name": "linuxpool",
        "count": 2,
        "vmSize": "Standard_D2_v2",
        "distro": "coreos",
        "availabilityProfile": "AvailabilitySet",
        "vnetSubnetId": "/subscriptions/<somesubsid>/resourceGroups/acsresourcegroup/providers/Microsoft.Network/virtualNetworks/k8s_vnet/subnets/k8s_subnet"
      }
    ],
    "linuxProfile": {
      "adminUsername": "azuradmineuser",
      "ssh": {
        "publicKeys": [
          {
            "keyData": "ssh-rsa ..."
          }
        ]
      }
    },
    "servicePrincipalProfile": {
      "clientId": "<someappid>",
      "secret": "<somepassword>"
    }
  }
}
```

The generate command takes a cluster definition and outputs a number of templates which describe your Kubernetes cluster. By default, generate will create a new directory named after your cluster nested in the _output directory.

```bash
acs-engine generate kubernetes.json
```

Deploy this to azure using the Azure cli

```bash
az group deployment create \
    --name "k8s_testing" \
    --resource-group "acsresourcegroup" \
    --template-file "./_output/k8s_testing/azuredeploy.json" \
    --parameters "./_output/k8s_testing/azuredeploy.parameters.json"
```

Edit your ```.kube/config``` file and add the cluster info from ```./_output/k8s_testing/kubeconfig/kubeconfig.westeurope.json

```bash
kubectl use-context k8s_testing
kubectl cluster-info
```