from flask import Flask, render_template, Response
import requests
import json
from dotenv import load_dotenv
import os
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from mpl_toolkits.basemap import Basemap

app = Flask(__name__)
load_dotenv()
DEFAULT_ID = 25544

@app.route('/')
def home():
    link = f"https://api.nasa.gov/planetary/apod?api_key={os.getenv('NASA_KEY')}"
    resp = requests.get(link)
    json_data = json.loads(resp.text)
    return render_template('index.html', 
                            img_url=json_data['url'], 
                            img_hd_url=json_data['hdurl'],
                            img_title=json_data['title'], 
                            img_explanation=json_data['explanation'])

@app.route('/satellite-tracker')
@app.route('/satellite-tracker/<sat_id>')
def test_table(sat_id=DEFAULT_ID):
    most_tracked = {"SPACE STATION":25544,"SES 1":36516,"NOAA 19":33591,"GOES 13":29155,"NOAA 15":25338,"NOAA 18":28654,"TERRA":25994,"AQUA":27424,"METOP-B":38771}
    return render_template('sat_tracker.html', entries=most_tracked, id=sat_id)

@app.route('/<sat_id>/sat-img.png')
def plot_img(sat_id):
    fig = make_map(sat_id)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def make_map(sat_id):
    observer_lat = 21.003422
    observer_lon = -101.272011
    observer_alt = 2012
    resp = requests.get(f"https://www.n2yo.com/rest/v1/satellite/positions/{ sat_id }/{ observer_lat }/{ observer_lon }/{ observer_alt }/300/&apiKey={ os.getenv('N2YO_KEY') }")
    lon, lat = FromSatJsonToXY(resp.text)

    fig = plt.figure(figsize=(8, 8))
    m = Basemap(projection='lcc', resolution=None,
                width=10E6, height=10E6, 
                lat_0=21.003422, lon_0=-101.272011,)
    m.etopo(scale=0.5, alpha=0.5)

    for i in range(len(lon)):
        x, y = m(lon[i], lat[i])
        plt.plot(x, y, 'ok', markersize=5)
    return fig

def FromSatJsonToXY(JsonData):
    Data = json.loads(JsonData)
    Positions = Data["positions"]
    Latitude = []
    Longitude = []
    for x in Positions:
        Longitude.append(x["satlongitude"]) 
        Latitude.append(x["satlatitude"])
    #Tupla = (Longitud, Latitude)
    return (Longitude, Latitude)

if __name__=="__main__":
    app.run('0.0.0.0', '8000', debug=True)