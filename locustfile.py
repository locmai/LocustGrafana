from locust import HttpLocust, TaskSet, task
from core import locustgraf

statsd = locustgraf.init_statsd()
locustgraf.init_influxdb_()
locustgraf.init_grafana_dashboard()


class ExampleTaskSet(TaskSet):
    @task
    def index(self):
        with statsd.timer('request_time'):
            response = self.client.get("/")
            statsd.incr('requests_{0}'.format(response.status_code))
        statsd.incr('requests')


class Locust(HttpLocust):
    host = "http://docs.locust.io/en/latest"
    task_set = ExampleTaskSet
    min_wait = 1000
    max_wait = 10000