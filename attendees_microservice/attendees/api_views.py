from django.http import JsonResponse
from common.json import ModelEncoder
from .models import Attendee, ConferenceVO, AccountVO
from django.views.decorators.http import require_http_methods
import json


# ----------------------------Encoders--------------------------#


class ConferenceVODetailEncoder(ModelEncoder):
    model = ConferenceVO
    properties = ["name", "import_href"]


class AttendeeDetailEncoder(ModelEncoder):
    model = Attendee
    properties = [
        "email",
        "name",
        "company_name",
        "created",
        "conference",
    ]

    encoders = {
        "conference": ConferenceVODetailEncoder(),
    }

    def get_extra_data(self, o):
        if AccountVO.objects.filter(email=o.email).count() > 0:
            return {"has_account": True}
        else:
            return {"has_account": False}


class AttendeeListEncoder(ModelEncoder):
    model = Attendee
    properties = [
        "name",
    ]


# --------------------------------------------------------------#


@require_http_methods(["GET", "POST"])
def api_list_attendees(request, conference_vo_id=None):
    """
    Lists the attendees names and the link to the attendee
    for the specified conference id.

    Returns a dictionary with a single key "attendees" which
    is a list of attendee names and URLS. Each entry in the list
    is a dictionary that contains the name of the attendee and
    the link to the attendee's information.

    {
        "attendees": [
            {
                "name": attendee's name,
                "href": URL to the attendee,
            },
            ...
        ]
    }
    """
    if request.method == "GET":
        attendees = Attendee.objects.filter(conference=conference_vo_id)
        return JsonResponse(
            {"attendees": attendees}, encoder=AttendeeListEncoder, safe=False
        )
    else:
        content = json.loads(request.body)

        try:
            # we're now using the slug from the url to get the full conference_href
            conference_href = f"/api/conferences/{conference_vo_id}/"
            # we can't access the id of conferences directly, so we are checking for the same href. Our ConferenceVO tracks the conference entity's href
            conference = ConferenceVO.objects.get(import_href=conference_href)
            content["conference"] = conference
        except ConferenceVO.DoesNotExist:
            return JsonResponse(
                {"message": "Invalid conference id"},
                status=400,
            )
        attendees = Attendee.objects.create(**content)
        return JsonResponse(
            attendees, encoder=AttendeeDetailEncoder, safe=False
        )


@require_http_methods(["GET", "DELETE", "PUT"])
def api_show_attendee(request, id):
    """
    Returns the details for the Attendee model specified
    by the id parameter.

    This should return a dictionary with email, name,
    company name, created, and conference properties for
    the specified Attendee instance.

    {
        "email": the attendee's email,
        "name": the attendee's name,
        "company_name": the attendee's company's name,
        "created": the date/time when the record was created,
        "conference": {
            "name": the name of the conference,
            "href": the URL to the conference,
        }
    }
    """
    if request.method == "GET":
        attendee = Attendee.objects.get(id=id)
        return JsonResponse(
            attendee, encoder=AttendeeDetailEncoder, safe=False
        )
    elif request.method == "DELETE":
        count, _ = Attendee.objects.filter(id=id).delete()
        return JsonResponse({"deleted": count > 0})
    else:
        # get content from the put
        content = json.loads(request.body)

        try:
            if "conference" in content:
                conference_href = f"/api/conferences/{content['conference']}/"
                conference = ConferenceVO.objects.get(
                    import_href=conference_href
                )
                content["conference"] = conference
        except ConferenceVO.DoesNotExist:
            return JsonResponse(
                {"message": "Invalid conference id"},
                status=400,
            )
        Attendee.objects.filter(id=id).update(**content)
        attendee = Attendee.objects.get(id=id)
        return JsonResponse(
            attendee, encoder=AttendeeDetailEncoder, safe=False
        )
