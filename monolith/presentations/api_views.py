from django.http import JsonResponse
from common.json import ModelEncoder
from .models import Presentation
from events.models import Conference
from django.views.decorators.http import require_http_methods
import json
from events.api_views import ConferenceListEncoder
import pika

# ----------------------------Encoders--------------------------#


class PresentationDetailEncoder(ModelEncoder):
    model = Presentation
    properties = [
        "presenter_name",
        "company_name",
        "presenter_email",
        "title",
        "synopsis",
        "created",
    ]
    encoders = {
        "conference": ConferenceListEncoder(),
    }

    def get_extra_data(self, o):
        return {"status": o.status.name}


class PresentationListEncoder(ModelEncoder):
    model = Presentation
    properties = [
        "title",
    ]

    def get_extra_data(self, o):
        return {"status": o.status.name}


# --------------------------------------------------------------#


def producer_message(queue, message):
    parameters = pika.ConnectionParameters(host="rabbitmq")
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue="queue")
    channel.basic_publish(
        exchange="",
        routing_key=queue,
        # body takes a string so if we're passing in a JSON/Dictionary, convert it with json.dumps
        body=json.dumps(message),
    )
    connection.close()


@require_http_methods(["PUT"])
def api_approve_presentation(request, pk):
    presentation = Presentation.objects.get(id=pk)
    presentation.approve()
    queue = "approval_queue"
    message = {
        "presenter_name": presentation.presenter_name,
        "presenter_email": presentation.presenter_name,
        "title": presentation.title,
    }
    producer_message(queue, message)
    return JsonResponse(
        presentation,
        encoder=PresentationDetailEncoder,
        safe=False,
    )


@require_http_methods(["PUT"])
def api_reject_presentation(request, pk):
    presentation = Presentation.objects.get(id=pk)
    presentation.reject()
    queue = "rejection_queue"
    message = {
        "presenter_name": presentation.presenter_name,
        "presenter_email": presentation.presenter_name,
        "title": presentation.title,
    }
    producer_message(queue, message)
    return JsonResponse(
        presentation,
        encoder=PresentationDetailEncoder,
        safe=False,
    )


@require_http_methods(["GET", "POST"])
def api_list_presentations(request, conference_id):
    """
    Lists the presentation titles and the link to the
    presentation for the specified conference id.

    Returns a dictionary with a single key "presentations"
    which is a list of presentation titles and URLS. Each
    entry in the list is a dictionary that contains the
    title of the presentation, the name of its status, and
    the link to the presentation's information.

    {
        "presentations": [
            {
                "title": presentation's title,
                "status": presentation's status name
                "href": URL to the presentation,
            },
            ...
        ]
    }
    """
    if request.method == "GET":
        presentations = Presentation.objects.filter(conference=conference_id)
        return JsonResponse(
            {"presentations": presentations},
            encoder=PresentationListEncoder,
            safe=False,
        )
    else:
        content = json.loads(request.body)
        # not top level, so check if parent is legit. assigning foreign key
        try:
            conference = Conference.objects.get(id=conference_id)
            content["conference"] = conference
        except Conference.DoesNotExist:
            return JsonResponse(
                {"message": "Invalid conference id"},
                status=400,
            )
        # status is a value object that wqe don't want to change within a post. This function auto assigns status property to it's default value
        presentation = Presentation.create(**content)
        return JsonResponse(
            presentation, encoder=PresentationDetailEncoder, safe=False
        )


@require_http_methods(["GET", "DELETE", "PUT"])
def api_show_presentation(request, id):
    """
    Returns the details for the Presentation model specified
    by the id parameter.

    This should return a dictionary with the presenter's name,
    their company name, the presenter's email, the title of
    the presentation, the synopsis of the presentation, when
    the presentation record was created, its status name, and
    a dictionary that has the conference name and its URL

    {
        "presenter_name": the name of the presenter,
        "company_name": the name of the presenter's company,
        "presenter_email": the email address of the presenter,
        "title": the title of the presentation,
        "synopsis": the synopsis for the presentation,
        "created": the date/time when the record was created,
        "status": the name of the status for the presentation,
        "conference": {
            "name": the name of the conference,
            "href": the URL to the conference,
        }
    }
    """
    if request.method == "GET":
        presentation = Presentation.objects.get(id=id)
        return JsonResponse(
            presentation,
            encoder=PresentationDetailEncoder,
            safe=False,
        )
    elif request.method == "DELETE":
        count, _ = Presentation.objects.filter(id=id).delete()
        return JsonResponse({"Deleted": count > 0})
    else:
        content = json.loads(request.body)
        # not top level, so check if parent is legit. assigning foreign key
        try:
            if "conference" in content:
                conference = Conference.objects.get(id=content["conference"])
                content["conference"] = conference
        except Conference.DoesNotExist:
            return JsonResponse(
                {"message": "Invalid conference id"},
                status=400,
            )
        Presentation.objects.filter(id=id).update(**content)
        presentation = Presentation.objects.get(id=id)
        return JsonResponse(
            presentation, encoder=PresentationDetailEncoder, safe=False
        )
