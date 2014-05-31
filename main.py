import os
from flask import Flask, render_template, request, redirect, make_response
from flask.ext.bootstrap import Bootstrap
from urllib2 import urlopen, Request
import json
from icalendar import Calendar, Event
import pytz
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
Bootstrap(app)

app.config['BOOTSTRAP_USE_MINIFIED'] = True
app.config['BOOTSTRAP_USE_CDN'] = True
app.config['BOOTSTRAP_FONTAWESOME'] = True

beeminder_client_id = os.environ["BEEMINDER_CLIENT_ID"]
site_redirect_address = os.environ["SITE_ADDRESS"] + "/oauth"

@app.route('/')
def index():
	return render_template('index.html', beeminder_client_id = beeminder_client_id, site_redirect_address = site_redirect_address)

@app.route("/oauth")
def oauth():
	access_token = request.args.get("access_token", None)
	if access_token == None:
		return redirect("/")
	data = urlopen("https://www.beeminder.com/api/v1/users/me.json?access_token=%s"%(access_token)).read()
	data = json.loads(data)
	return redirect("/calendar/%s?access_token=%s"%(data["username"], access_token))

@app.route('/calendar/<username>')
def calendar(username):
	access_token = request.args.get("access_token")

	data = urlopen("https://www.beeminder.com/api/v1/users/%s/goals.json?access_token=%s"%(username, access_token)).read()
	data = json.loads(data)

	cal = Calendar()
	cal.add('prodid', '-//Beeminder calendar//tevp.net//')
	cal.add('version', '2.0')
	cal.add('X-WR-CALNAME', 'Beeminder Calendar for %s'%username)

	for goal in data:
		startdate = datetime.fromtimestamp(goal["losedate"]).date()
		enddate = startdate + timedelta(days = 1)
		title = goal["title"]
		event = Event()
		event.add('summary', "%s fail day" % title)
		event.add('dtstart', startdate)
		event.add('dtend', enddate)
		event.add('last-modified', datetime.now())
		event['uid'] = hashlib.md5(title + str(startdate)).hexdigest()
		cal.add_component(event)

	resp = make_response(cal.to_ical())
	resp.headers["Content-Type"] = "text/Calendar"
	resp.headers["Cache-Control"] = "no-cache, must-revalidate"
	resp.headers["Expires"] = "Sat, 26 Jul 1997 05:00:00 GMT"
	return resp

if '__main__' == __name__:
	app.run(debug=True, port=8080)
