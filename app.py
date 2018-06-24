import os
import requests
from flask import Flask
import pickle
from todoist.api import TodoistAPI
import re
from datetime import datetime, timedelta

app = Flask(__name__)

def send_notification(message):
    pushover_token = os.getenv('PUSHOVER_TOKEN')
    pushover_url = 'https://api.pushover.net/1/messages.json'
    params = {
        'token': pushover_token,
        'user': 'uga9w2s6wJsnGUwTjpmJnyMQnV6E5q',
        'priority': -1,
        'message': message,
        'title': 'Productivity'
    }
    requests.post(pushover_url, params=params)


def get_pulse_change():
    rescuetime_token = os.getenv('RESCUETIME_TOKEN')
    url = 'https://www.rescuetime.com/anapi/daily_summary_feed'
    params = {'key': rescuetime_token}
    resp = requests.get(url, params=params)
    json_response = resp.json()
    latest, previous, *_ = json_response
    rescuetime_change = latest['productivity_pulse'] - previous['productivity_pulse']
    done, total_habits = get_streak()
    streak_change = get_streak_change(done)
    change = rescuetime_change/100.0 * (100-total_habits) + streak_change
    change = round(change, 1)
    return "{:+}%".format(change)


def get_token():
    token = os.getenv('TODOIST_APIKEY')
    return token


def is_habit(text):
    return re.search(r'\[day\s(\d+)\]', text)


def is_today(text):
    today = (datetime.utcnow() + timedelta(1)).strftime("%a %d %b")
    return text[:10] == today

def is_due(text):
    yesterday = datetime.utcnow().strftime("%a %d %b")
    return text[:10] == yesterday


def get_streak():
    todoist_token = get_token()
    api = TodoistAPI(todoist_token)
    api.sync()
    tasks = api.state['items']
    total = 0
    done = 0
    for task in tasks:
        if (task['due_date_utc']) and is_habit(task['content']):
            if(is_today(task['due_date_utc']) or is_due(task['due_date_utc'])):
                habit = is_habit(task['content'])
                streak = int(habit.group(1))
                if streak:
                    done += 1
                total += 1
    return done, total    

def get_streak_change(streak):
    fp = open('data.pkl', 'rb')
    details = pickle.load(fp)
    fp.close()
    last_done = details['habits']
    change = streak - last_done
    details = {'habits': streak}
    fp = open('data.pkl', 'wb')
    pickle.dump(details, fp)
    fp.close()
    return change


@app.route('/')
def index():
    change = get_pulse_change()
    # send_notification(change)
    return change


@app.route('/reset')
def reset():
    details = {'habits': 0}
    pickle.dump(details, open('data.pkl', 'wb'))
    return 'Done.'


if __name__ == '__main__':
    app.run()
