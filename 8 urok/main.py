import os
import json
import requests
import folium
from geopy import distance
from flask import Flask, render_template_string
from dotenv import load_dotenv


app = Flask(__name__)
load_dotenv()


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lat, lon


def create_map(coords_user, coffee_list):
    map_ = folium.Map(location=[float(coords_user[0]), float(coords_user[1])], zoom_start=14)

    folium.Marker(
        location=[float(coords_user[0]), float(coords_user[1])],
        popup='Вы находитесь здесь',
        icon=folium.Icon(color='blue')
    ).add_to(map_)

    for coffee in coffee_list:
        folium.Marker(
            location=[float(coffee['latitude']), float(coffee['longitude'])],
            popup=coffee['title'],
            icon=folium.Icon(color='red')
        ).add_to(map_)

    return map_ 


def main():
    with open("coffee.json", "r", encoding="CP1251") as my_file:
        file_contents = my_file.read()
    format_contents = json.loads(file_contents)

    apikey = os.getenv('API_KEY')
    location = input('Где вы находитесь? ')
    coords_user = fetch_coordinates(apikey, location)

    coffee_list = []

    for item in format_contents:
        title = item['Name']
        latitude = item['Latitude_WGS84']
        longitude = item['Longitude_WGS84']
        coords_coffee = (float(latitude), float(longitude))
        dist = distance.distance(coords_user, coords_coffee).km

        coffee_info = {
            'title': title,
            'distance': dist,
            'latitude': latitude,
            'longitude': longitude
        }
        coffee_list.append(coffee_info)

    sorted_coffee = sorted(coffee_list, key=lambda x: x['distance'])[:5]
    map_ = create_map(coords_user, sorted_coffee)
    map_html = map_._repr_html_()

    return render_template_string("""
        <html>
            <head>
                <title>Карта кофеен</title>
            </head>
            <body>
                {{ map_html|safe }}
            </body>
        </html>
    """, map_html=map_html)


app.add_url_rule('/', 'render_map', main)

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
