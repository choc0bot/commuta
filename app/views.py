from app import app
from flask import render_template, session, url_for, redirect, request
from stravalib.client import Client
import config as cfg

TOKEN = ""
MY_STRAVA_CLIENT_ID = cfg.MSCID
MY_STRAVA_CLIENT_SECRET = cfg.MYCS

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',title='Home')


@app.route('/login')
def strava_auth():
  client = Client()
  authorize_url = client.authorization_url(client_id=3982, redirect_uri='http://127.0.0.1:5000/authorized')
  #return redirect(authorize_url)
  return render_template('login.html', url=authorize_url)

@app.route('/authorized',  methods = ['GET', 'POST'])
def authorized():
  global TOKEN
  # Extract the code from your webapp response
  state = request.args['state']
  code = request.args['code']
  client = Client()
  access_token = client.exchange_code_for_token(client_id=MY_STRAVA_CLIENT_ID, client_secret=MY_STRAVA_CLIENT_SECRET, code=code)

  TOKEN = access_token
  # Now store that access token somewhere (a database?)
  client.access_token = access_token
  athlete = client.get_athlete()
  return render_template('success.html', athlete=athlete, token=access_token)


@app.route('/commute')
def commute():
  global TOKEN
  if TOKEN == "":
    return redirect('/login')
  else:
    client = Client(TOKEN)
    athlete = client.get_athlete()
    activities = client.get_activities()
    commute_count = 0
    for a in activities:
      if a.name == "Commute":
        commute_count += 1
    commute_saving = 3.58 * commute_count

    return render_template('commute.html', firstname=athlete.firstname, lastname=athlete.lastname, athlete=athlete, total_commutes=commute_count, total_savings=commute_saving)


def login():
    app_url = 'http://127.0.0.1:5000'
    callback_url = app_url + url_for('oauth_authorized')
    return strava.authorize(callback=callback_url)
