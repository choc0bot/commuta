from app import app, db
from flask import render_template, flash, session, url_for, redirect, request, g
from stravalib.client import Client
import config as cfg
import datetime
from .models import commutra
from .forms import LoginForm
from .forms import SettingsForm

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
  user = commutra(token=access_token)
  if user.is_authenticated():
    flash('Welcome back')
  else:
    db.session.add(user)
    db.session.commit()
    flash('Your changes have been saved.')
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
    settings = commutra.query.filter_by(token=TOKEN).first()
    commute_count = 0
    for act in activities:
      if "commute" in act.name.lower():
        commute_count += 1
    commute_saving = settings.goal_savings * commute_count
    commute_goal = settings.goal_value - commute_saving
    commute_goal_percent = int(round((commute_saving/settings.goal_value)*100))

    return render_template('commute.html', firstname=athlete.firstname, lastname=athlete.lastname, athlete=athlete, total_commutes=commute_count, total_savings=commute_saving, goal=commute_goal, percent_complete=commute_goal_percent)

@app.route('/commute_details')
def commute_details():
  global TOKEN
  if TOKEN == "":
    return redirect('/login')
  else:
    client = Client(TOKEN)
    activities = client.get_activities()
    distance_count = 0
    commute_count = 0
    elapsed_count = 0
    for act in activities:
      if "commute" in act.name.lower():
        commute_count += 1
        distance_count += float(act.distance)/1000
        elapsed_count += datetime.timedelta.total_seconds(act.elapsed_time)
    return render_template('commute_details.html', total_commutes=commute_count, total_distance=round(distance_count,2),  total_elapsed_time=str(datetime.timedelta(seconds=elapsed_count)))

#def login():
#    app_url = 'http://127.0.0.1:5000'
#    callback_url = app_url + url_for('oauth_authorized')
#    return strava.authorize(callback=callback_url)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
  global TOKEN
  form = SettingsForm()
  if form.validate_on_submit():
    commute.commute_tag = form.commute_tag.data
    commute.commute_string = form.commute_string.data
    commute.goal_name = form.goal_string.data
    commute.goal_value = form.goal_number.data
    commute.goal_savings = form.savings.data
    #user = commutra(token=TOKEN,commute_tag=commute.commute_tag,commute_string=commute.commute_string,goal_name=commute.goal_name,goal_value=commute.goal_value,goal_savings=commute.goal_savings)
    user = commutra(token=TOKEN)
    if user.is_authenticated():
      user = commutra.query.filter_by(token=TOKEN).first()
      user.commute_tag = commute.commute_tag
      user.commute_string=commute.commute_string
      user.goal_name=commute.goal_name
      user.goal_value=commute.goal_value
      user.goal_savings=commute.goal_savings
      db.session.commit()
      flash('Your changes have been saved.')
      flash('Settings saved')
      return redirect('/index')
  return render_template('settings.html',title='Settings',form=form)

@app.route('/user', methods=['GET', 'POST'])
def user():
  form = LoginForm()
  if form.validate_on_submit():
    flash('Login requested for OpenID="%s", remember_me=%s' %
          (form.openid.data, str(form.remember_me.data)))
    return redirect('/index')
  return render_template('login_user.html', 
                         title='Sign In',
                         form=form,
                         providers=app.config['OPENID_PROVIDERS'])