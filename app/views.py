from app import app, db, lm
from flask import render_template, flash, session, url_for, redirect, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from stravalib.client import Client, unithelper
import config as cfg
import datetime
import calendar
from collections import Counter
from .models import commutra
from .forms import LoginForm
from .forms import SettingsForm
import json

TOKEN = ""
MY_STRAVA_CLIENT_ID = cfg.MSCID
MY_STRAVA_CLIENT_SECRET = cfg.MYCS

@app.template_filter()
def datetimefilter(value, time_format='%Y-%m-%d'):
    """convert a datetime to a different format."""
    return value.strftime(time_format)

@app.template_filter()
def dayfilter(value):
    """convert a datetime to a different format."""
    return calendar.day_name[value]

@app.template_filter()
def monthfilter(value):
    """convert a datetime to a different format."""
    return calendar.month_name[value]

@app.template_filter()
def datefilter(value, time_format='%m'):
    """convert a datetime to a different format."""
    return value.strftime(time_format)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@lm.user_loader
def load_user(TOKEN):
    return commutra.query.get(TOKEN)

@app.route('/login')
def strava_auth():
    client = Client()
    authorize_url = client.authorization_url(client_id=3982, redirect_uri='http://127.0.0.1:5000/authorized')
    return redirect(authorize_url)
    #return render_template('login.html', url=authorize_url)

@app.route('/logout')
#@login_required
def logout():
    TOKEN=""
    logout_user()
    return redirect(url_for('index'))

@app.route('/authorized',  methods = ['GET', 'POST'])
def authorized():
    global TOKEN
    # Extract the code from your webapp response
    #state = request.args['state']
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
    return render_template('index.html', athlete=athlete, token=access_token)

def check_monthly(date_to_test, local_time):
    if date_to_test.month == (local_time.month):
        return True
    if date_to_test.year < (local_time.year):
        return False
    elif date_to_test.month < (local_time.month - 1):
        return False
    elif date_to_test.day < local_time.day:
        return False
    else:
        return True

def convert_timedelta(delta_to_convert):
    seconds = delta_to_convert.total_seconds()
    #hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return minutes

@app.route('/commute')
def commute():
    global TOKEN
    if TOKEN == "":
        return redirect('/login')
    if commutra.query.get(TOKEN) == False:
        user = commutra(token=TOKEN)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:
        client = Client(TOKEN)
        athlete = client.get_athlete()
        activities = client.get_activities()
        settings = commutra.query.filter_by(token=TOKEN).first()
        flag = settings.commute_tag
        local_time = datetime.date.today()
        equator_length = 40075
        monthly_rides = []
        monthly_savings = []
        dow_rides = []
        commute_count = 0
        commute_distance = 0.0
        day_count_list = []
        commute_saving = 0
        commute_goal = 0
        commute_goal_percent = 0
        for act in activities:
            if flag == True:
                if act.commute == True:
                    commute_count += 1
                    commute_distance += float(unithelper.kilometers(act.distance))
                    ride_date = act.start_date_local
                    if check_monthly(act.start_date_local, local_time):
                        monthly_rides.append([ride_date, convert_timedelta(act.elapsed_time)])
            else:
                if settings.commute_string != None:
                    if settings.commute_string.lower() in act.name.lower():
                        commute_count += 1
                        commute_distance += float(unithelper.kilometers(act.distance))
                        ride_date = act.start_date_local
                        monthly_savings.append(ride_date.month)
                        #if check_monthly(act.start_date_local, local_time):
                        monthly_rides.append([ride_date, convert_timedelta(act.elapsed_time)])
                        dow_rides.append(int(ride_date.weekday()))
                    day_count_list  = list(Counter(dow_rides).items())
                    month_count_list =  list(Counter(monthly_savings).items())
                    total_carbon = round((commute_count * settings.carbon_number) / 1000,2)
                    total_carbon_trees = round((commute_count * settings.carbon_number) / 22100, 2)
                    #day_count_= list(day_count_l).item()
                    commute_saving = settings.goal_savings * commute_count
                    commute_goal = settings.goal_value - commute_saving
                    commute_goal_percent = int(round((commute_saving/settings.goal_value)*100))
                    #monthly_rides_json = json.dumps(monthly_rides)
                    commute_goal_title = settings.goal_name
                    round_the_world = equator_length / commute_distance

    return render_template('commute.html',  total_distance = round(commute_distance,2),
                                            total_carbon = total_carbon,
                                            day_count = day_count_list,
                                            monthly_savings = month_count_list,
                                            monthly_rides = monthly_rides,
                                            firstname = athlete.firstname,
                                            lastname = athlete.lastname,
                                            athlete = athlete,
                                            total_commutes = commute_count,
                                            total_savings = commute_saving,
                                            goal = commute_goal,
                                            percent_complete = commute_goal_percent,
                                            goal_title = commute_goal_title,
                                            round_the_world = round_the_world,
                                            total_carbon_trees = total_carbon_trees)

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
        commute.carbon_number = form.carbon_number.data
        #user = commutra(token=TOKEN,commute_tag=commute.commute_tag,commute_string=commute.commute_string,goal_name=commute.goal_name,goal_value=commute.goal_value,goal_savings=commute.goal_savings)
        user = commutra(token=TOKEN)
        if user.is_authenticated():
            user = commutra.query.filter_by(token=TOKEN).first()
            user.commute_tag = commute.commute_tag
            user.commute_string=commute.commute_string
            user.goal_name=commute.goal_name
            user.goal_value=commute.goal_value
            user.goal_savings=commute.goal_savings
            user.carbon_number=commute.carbon_number
            db.session.commit()
            flash('Your changes have been saved.')
            flash('Settings saved')
            return redirect('/index')
    user = commutra(token=TOKEN)
    if user.is_authenticated():
        user = commutra.query.filter_by(token=TOKEN).first()
        return render_template( 'settings.html',
                                title='Settings',user=user,
                                form=SettingsForm(  commute_tag=user.commute_tag,
                                                    commute_string=user.commute_string,
                                                    goal_string=user.goal_name,
                                                    goal_number=user.goal_value,
                                                    savings=user.goal_savings,
                                                    carbon_number=user.carbon_number))
    return render_template('settings.html',title='Settings',form=form)
