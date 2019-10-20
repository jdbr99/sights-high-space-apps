from flask import Flask, render_template, Response, request, send_file
from flask_wtf import FlaskForm
from wtforms import SubmitField, FloatField, IntegerField
from wtforms.validators import DataRequired
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

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_KEY')
app.config['CLIENT_IMAGES'] = '/home/jdbr/dev/sights-high-space-apps/static/client/img' 

DEFAULT_ID = 25544

class UsrCoordsForm(FlaskForm):
    usr_lat = FloatField('Latitude', validators=[DataRequired()], default=0)
    usr_lon = FloatField('Latitude', validators=[DataRequired()], default=0)
    usr_sat_id = IntegerField('Satellite ID', validators=[DataRequired()], default=25544)
    submit = SubmitField('Plot')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/apotd')
def apotd():
    link = f"https://api.nasa.gov/planetary/apod?api_key={os.getenv('NASA_KEY')}"
    resp = requests.get(link)
    json_data = json.loads(resp.text)
    return render_template('potd.html', 
                            img_url=json_data['url'], 
                            img_hd_url=json_data['hdurl'],
                            img_title=json_data['title'], 
                            img_explanation=json_data['explanation'])

@app.route('/satellite-tracker', methods=["GET"])
@app.route('/satellite-tracker/', methods=["GET"])
def test_table(sat_id=DEFAULT_ID):
    most_tracked = {"SPACE STATION":25544, "Meteor M2": 40069,"SES 1":36516,"NOAA 19":33591,"NOAA 15":25338,"AGILE": 31135,"SUOMI NPP": 37849,"AQUA":27424,"METOP-B":38771}
    # altitude
    resp = requests.get(f"https://www.n2yo.com/rest/v1/satellite/positions/{ request.args.get('usr_sat_id') }/{ request.args.get('usr_lat') }/{ request.args.get('usr_lon') }/{ request.args.get('usr_alt') }/300/&apiKey={ os.getenv('N2YO_KEY') }")
    _,_,alt = FromSatJsonToXYZ(resp.text)
    # tle
    tle = requests.get(f"https://www.n2yo.com/rest/v1/satellite/tle/{ request.args.get('usr_sat_id') }&apiKey={ os.getenv('N2YO_KEY') }")
    # print(tle.text)
    return render_template('sat_tracker.html',
                            entries=most_tracked,
                            sat_id=request.args.get('usr_sat_id'),
                            usr_lat=request.args.get('usr_lat'),
                            usr_lon=request.args.get('usr_lon'),
                            sat_alt=alt[0],
                            sat_vel=SacarVelocidad(alt[0]),
                            sat_rpd_avg=FromTLEToDat(tle.text))

@app.route('/<usr_lat>/<usr_lon>/<sat_id>/sat-img.png')
def plot_img(usr_lat, usr_lon, sat_id):
    fig = make_map(sat_id, usr_lat, usr_lon)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

@app.route('/logo.png')
def logo():
    return send_file('/home/jdbr/dev/sights-high-space-apps/static/client/img/logo.png')

@app.route('/back.jpg')
def back():
    return send_file('/home/jdbr/dev/sights-high-space-apps/static/client/img/back.jpg')

def make_map(sat_id, usr_lat, usr_lon):
    observer_lat = usr_lat
    observer_lon = usr_lon
    observer_alt = 2012
    resp = requests.get(f"https://www.n2yo.com/rest/v1/satellite/positions/{ sat_id }/{ observer_lat }/{ observer_lon }/{ observer_alt }/300/&apiKey={ os.getenv('N2YO_KEY') }")
    lon, lat,_ = FromSatJsonToXYZ(resp.text)

    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(1,1,1)
    fig.set_facecolor((100/255, 100/255, 100/255))
    m = Basemap(projection='ortho', resolution=None, lat_0=lat[0], lon_0=lon[0])
    m.bluemarble(scale=0.5)
    
    x, y = m(lon[0], lat[0])
    ax.plot(x,y, color='red', marker='o', markersize=5)
    for i in range(1,len(lon)-1):
        x, y = m(lon[i], lat[i])
        ax.plot(x, y, color='red', marker='.', markersize=1)
    x, y = m(lon[-1], lat[-1])
    ax.plot(x, y, color='red', marker="D", markersize=5)
    return fig

def FromSatJsonToXYZ(JsonData):
    Data = json.loads(JsonData)
    Positions = Data["positions"]
    Latitude = []
    Longitude = []
    Altitude = []
    for x in Positions:
        Longitude.append(x["satlongitude"]) 
        Latitude.append(x["satlatitude"])
        Altitude.append(x["sataltitude"])
    return (Longitude, Latitude, Altitude)

def SacarVelocidad(Altitud):
    Radio = (6371. + Altitud) #* (10**3)
    ConstGrav = 6.67408 #* (10**(-11))
    MasaTierra = 5.972 #* (10**24)
    Velocidad = ((ConstGrav * MasaTierra * (10**10))/Radio) ** (1/2)
    
    return Velocidad

def EsEntero(Valor):
    ValorEntero = int(Valor)
    if Valor > ValorEntero:
        return False
    return True


def CortarDecimales(Valor):
    Valor *= 100000000
    Valor = int(Valor)
    Valor = float(Valor)
    Valor /= 100000000
    
    return Valor


def FromTLEToDat(TLEData):
    #Esto es necesario porque json.loads se vuelve loco si se conserva el '\r'
    TLEData = TLEData.replace('\r','')
    TLEData = TLEData.replace('\n',' ')
    
    Data = json.loads(TLEData)
    Values = Data["tle"].split()
    
    if EsEntero(float(Values[-1])):
        return float(Values[-2])
    
    Temp = CortarDecimales(float(Values[-1]))
    return Temp

if __name__=="__main__":
    app.run('0.0.0.0', '8000', debug=True)