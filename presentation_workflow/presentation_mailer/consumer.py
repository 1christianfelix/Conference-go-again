import json
import pika
import django
import os
import sys
from django.core.mail import send_mail


sys.path.append("")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "presentation_mailer.settings")
django.setup()


def process_approval(ch, method, properties, body):
    body = json.loads(body)
    send_mail(
        "Your presentation ahs been accepted",
        f"{body['presenter_name']}, we're happy to tell you that your presentation {body['title']} has been accepted",
        "admin@conference.go",
        [body["presenter_email"]],
        fail_silently=False,
    )


def process_rejection(ch, method, properties, body):
    body = json.loads(body)
    send_mail(
        "Your presentation ahs been rejected",
        f"{body['presenter_name']}, we're happy to tell you that your presentation {body['title']} has been rejected",
        "admin@conference.go",
        [body["presenter_email"]],
        fail_silently=False,
    )


parameters = pika.ConnectionParameters(host="rabbitmq")
connection = pika.BlockingConnection(parameters)

channel = connection.channel()
channel.queue_declare(queue="approval_queue")
channel.basic_consume(
    queue="approval_queue",
    on_message_callback=process_approval,
    auto_ack=True,
)


channel = connection.channel()
channel.queue_declare(queue="rejection_queue")
channel.basic_consume(
    queue="rejection_queue",
    on_message_callback=process_rejection,
    auto_ack=True,
)

channel.start_consuming()


# region Refactored version

# import json
# import pika
# import django
# import os
# import sys
# from django.core.mail import send_mail
# ​
# ​
# sys.path.append("")
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "presentation_mailer.settings")
# django.setup()
# ​
# # Setup Django environment
# django.setup()
# ​
# # Define message processing function
# def process_message(ch, method, properties, body):
#     print("What is the ch parameter: ", ch)
#     print("\nWhat is the method parameter: ", method)
#     print("\nWhat is the properties parameter: ", properties)
#     print("\nWhat is the body parameter: ", body)
# ​
#     body = json.loads(body)
#     subject = None
#     message = None
#     if method.routing_key == "approval_queue":
#         subject = "Your presentation has been accepted"
#         message = f"{body['presenter_name']}, we're happy to tell you that your presentation {body['title']} has been accepted"
#     elif method.routing_key == "rejection_queue":
#         subject = "Your presentation has been rejected"
#         message = f"{body['presenter_name']}, we're sorry to inform you that your presentation {body['title']} has been rejected"
# ​
#     if subject and message:
#         send_mail(
#             subject=subject,
#             message=message,
#             from_email="admin@conference.go",
#             recipient_list=[body["presenter_email"]],
#             fail_silently=False,
#         )
#     # in the api_views, channel.basic_publish created a dictionary with keys that get passed into a function called channel.basic_consume that parses the data into properties that are sent as arguments to the callback function 'process_message'
#     # process_message is taking in those arguments.
#     # the method argument is an instance of the Basic.Deliver class from the pika library and contains a property called "routing_key", which has the name of the queue that sent the message to be consumed.
#     # in the api_views.py, we defined what routing_key would be in the channel.basic_publish().
# ​
# ​
# # Connect to RabbitMQ
# parameters = pika.ConnectionParameters(host="rabbitmq")
# connection = pika.BlockingConnection(parameters)
# channel = connection.channel()
# ​
# # Declare and consume from queues
# for queue in ["approval_queue", "rejection_queue"]:
#     channel.queue_declare(queue=queue)
#     # consume the message that was just to the queue from channel.basic_publish in the views function from the queue
#     channel.basic_consume(
#         queue=queue,
#         on_message_callback=process_message,
#         auto_ack=True,
#     )
# ​
# # Start consuming messages
# channel.start_consuming()

# endregion
