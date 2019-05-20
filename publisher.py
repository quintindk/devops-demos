#!/usr/bin/env python
import os
import time
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
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