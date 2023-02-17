from json import JSONEncoder
from datetime import datetime
from django.db.models import QuerySet


class QuerySetEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, QuerySet):
            return list(o)
        else:
            return super().default(o)


class DateEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        else:
            return super().default(o)


class ModelEncoder(DateEncoder, QuerySetEncoder, JSONEncoder):
    encoders = {}

    def default(self, o):
        if isinstance(o, self.model):
            d = {}
            if hasattr(o, "get_api_url"):
                d["href"] = o.get_api_url()
            for property in self.properties:
                value = getattr(o, property)
                # if encoder has a property that requires another encoder
                if property in self.encoders:
                    # the value at this point must be an instance of a class that needs encoding
                    encoder = self.encoders[property]
                    # send that value through the encoder's default encoder function to return a parsable value
                    value = encoder.default(value)
                d[property] = value
            # for one off values. Stuff ljke status and states are classes with 1 value we want.
            # only need them for specfic request
            d.update(self.get_extra_data(o))
            return d
        else:
            return super().default(o)

    def get_extra_data(self, o):
        return {}
