from .keys import PEXELS_API_KEY, OPEN_WEATHER_API_KEY
import requests
import json


def get_photo(city, state):
    # print("here, ", city, state)
    headers = {"Authorization": PEXELS_API_KEY}
    url = "https://api.pexels.com/v1/search"
    parameters = {"query": f"{city}, {state}", "per_page": "1"}
    # print("before request")
    r = requests.get(url, params=parameters, headers=headers)
    # print(type(r))
    # print("after request")
    # print("\n")
    # print(r.json())
    # print("\n")
    content = r.json()
    # print(content.keys())
    try:
        photo_url = content["photos"][0]["src"]["original"]
        # print(photo_url)
        return photo_url
    except:
        return "No Photos Found"


def get_weather_data(city, state):
    # geocoding
    headers = {"Authorization": OPEN_WEATHER_API_KEY}
    url = "http://api.openweathermap.org/geo/1.0/direct"
    parameters = {
        "q": city + "," + state + "," + "USA",
        "appid": OPEN_WEATHER_API_KEY,
    }
    r = requests.get(url, params=parameters, headers=headers)
    content = r.json()
    lat = content[0]["lat"]
    lon = content[0]["lon"]

    url = "https://api.openweathermap.org/data/2.5/weather"
    parameters = {
        "lat": lat,
        "lon": lon,
        "appid": OPEN_WEATHER_API_KEY,
        "units": "imperial",
    }

    r = requests.get(url, params=parameters, headers=headers)
    content = r.json()
    try:
        temp = content["main"]["temp"]
        description = content["weather"][0]["description"]
        return {"temp": temp, "description": description}
    except:
        return None
