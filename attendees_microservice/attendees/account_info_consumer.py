from datetime import datetime
import json
import pika
from pika.exceptions import AMQPConnectionError
import django
import os
import sys
import time


sys.path.append("")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendees_bc.settings")
django.setup()

from attendees.models import AccountVO

while True:
    try:

        def update_AccountVO(ch, method, properties, body):
            content = json.loads(body)
            account_details = {
                "first_name": content["first_name"],
                "last_name": content["last_name"],
                "email": content["email"],
                "is_active": content["is_active"],
                "updated": datetime.fromisoformat(content["updated"]),
            }
            if content["is_active"]:
                AccountVO.objects.update_or_create(
                    email=content["email"], defaults=account_details
                )
            else:
                AccountVO.objects.filter(email=content["email"]).delete()

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq")
        )
        channel = connection.channel()
        channel.exchange_declare(
            exchange="account_info", exchange_type="fanout"
        )
        result = channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange="account_info", queue=queue_name)
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=update_AccountVO,
            auto_ack=True,
        )
        print(" [*] Waiting for messages. To exit press CTRL+C")
        channel.start_consuming()

    except AMQPConnectionError:
        print("Could not connect to RabbitMQ")
        time.sleep(2.0)
