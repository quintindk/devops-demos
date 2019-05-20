#!/usr/bin/env python
import os
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='demo')

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)

channel.basic_consume('demo',
                    callback,
                    auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()