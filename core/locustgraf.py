from requests.exceptions import ConnectionError

import time
import json
import requests
from statsd import TCPStatsClient

from core.config import Config


def init_statsd():
    statsd = TCPStatsClient(host= Config.STATSD_HOST,
                         port= Config.STATSD_PORT,
                         prefix= Config.STATSD_PREFIX)
    return statsd


def init_grafana_dashboard():
    grafana_url = Config.GRAFANA_URL

    grafana_user = Config.GRAFANA_USER
    grafana_password = Config.GRAFANA_PASSWORD

    payload = {"user": grafana_user, "password": grafana_password}
    headers = {'Content-Type': 'application/json'}

    session = requests.Session()

    response = post_with_retries(session, "{0}/login".format(grafana_url), payload, headers)
    data = response.json()

    #print(data)

    if 'logged in' == data['message'].lower():
        # Create data source
        payload = {"access": "direct",
                   "database": "statsd",
                   "isDefault": True,
                   "name": "statsd",
                   "password": "root",
                   "type": "influxdb_08",
                   "url": Config.INFLUXDB_HOST,
                   "user": "root"
                   }

        response = session.put("{0}/api/datasources".format(grafana_url) , data=json.dumps(payload), headers=headers)
        print(response.json())

        dashboard_json = open('dashboard.json').read()
        response = session.post('{0}/api/dashboards/db/'.format(grafana_url), data=dashboard_json, headers=headers)
        print(response.json())


def init_influxdb():
    influxdb_url = Config.INFLUXDB_HOST

    session = requests.Session()

    http_status = [200, 400, 403, 404, 500, 503]

    prefix = Config.STATSD_PREFIX
    influxdb_user = Config.INFLUX_USER
    influxdb_password = Config.INFLUX_PASSWORD
    post_url = '{0}/db/statsd/series?u={1}&p={2}'.format(influxdb_url, influxdb_user, influxdb_password)

    for status in http_status:
        print("adding counter for {0}".format(str(status)))
        payload = [{
                    "name" : "{0}.requests_{1}.counter".format(prefix, status),
                    "columns" : ["value"],
                    "points" : [[0]]
                   }]
        post_with_retries(session, post_url, payload, {'Content-Type': 'application/json'})


def post_with_retries(session, url, payload, headers):
    backoff = 0
    retries = 10
    while retries > 0:
        try:
            response = session.post(url, data=json.dumps(payload), headers=headers)
            print(response.status_code)
            return response
            break
        except ConnectionError as e:
            print("Retrying in {0} seconds".format(str(2**backoff)))
            time.sleep(2**backoff)
            backoff += 1

        retries -= - 1
    if retries == 0:
        raise e