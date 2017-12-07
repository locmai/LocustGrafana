from requests.exceptions import ConnectionError

import os
import json
import requests

from Core import Config

def init_grafana_dashboard():
    grafana_url = os.environ.get('GRAFANA_URL', Config.GRAFANA_URL)

    grafana_user = os.environ.get('GRAFANA_URL', Config.GRAFANA_USER)
    grafana_password = os.environ.get('GRAFANA_URL', Config.GRAFANA_PASSWORD)

    payload = {"user": grafana_user, "email": "", "password": grafana_password}
    headers = {'Content-Type': 'application/json'}

    session = requests.Session()

    response = post_with_retries(session, "%s/login" % grafana_url, payload, headers)
    data = response.json()

    print(data)

    if 'logged in' == data['message'].lower():
        # Create data source
        payload = {"access": "direct",
                   "database": "statsd",
                   "isDefault": True,
                   "name": "statsd",
                   "password": "root",
                   "type": "influxdb_08",
                   "url": os.environ.get('INFLUXDB_HOST', Config.INFLUXDB_HOST),
                   "user": "root"
                   }

        response = session.put("%s/api/datasources" % grafana_url, data=json.dumps(payload), headers=headers)
        print(response.json())

        dashboard_json = open('dashboard.json').read()
        response = session.post('%s/api/dashboards/db/' % grafana_url, data=dashboard_json, headers=headers)
        print(response.json())


def post_with_retries(session, url, payload, headers):
    backoff = 0
    retries = 10
    while retries > 0:
        try:
            response = session.post(url, data=json.dumps(payload), headers=headers)
            print(response.text)
            return response
            break
        except ConnectionError as e:
            print("Retrying in %s seconds" %2**backoff)
            time.sleep(2**backoff)
            backoff += 1

        retries -= - 1
    if retries == 0:
        raise e