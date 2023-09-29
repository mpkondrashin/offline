import requests
import time
from datetime import datetime, timedelta

url_base = 'https://api.xdr.trendmicro.com'
token = 'YOUR TOKEN'

date_time_format = '%Y-%m-%dT%H:%M:%SZ'

class VOne:
    def __init__(self, base, token):
        self.base = base
        self.token = token

    def get(self, link, params, headers):
        headers['Authorization'] = 'Bearer ' + self.token
        while True:
            r = requests.get(link, params=params, headers=headers)
            if r.status_code == 429:
                # https://automation.trendmicro.com/xdr/Guides/API-Request-Limits
                time.sleep(120)
                continue
            if r.status_code == 200:
                return r
            raise RuntimeError(r.text)

    def iterate_endpoints(self):
        headers = {'TMV1-Query': "not (endpointName eq 'nonexistent')"}
        params = {'top': '200'}
        link = self.base + '/v3.0/eiqs/endpoints'
        while link is not None:
            r = self.get(link, params=params, headers=headers)
            for item in r.json()["items"]:
                yield item['agentGuid'], item['endpointName']['value']
            param = {}
            link = r.json().get('nextLink')

    def iterate_offline(self, days):
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        params = {
            'startDateTime': start_date.strftime(date_time_format),
            'endDateTime': end_date.strftime(date_time_format),
            'top': '50',
            'mode': 'countOnly'
        }
        for guid, hostname in self.iterate_endpoints():
            headers = {'TMV1-Query': f"endpointGuid:{guid}"}
            r = self.get(self.base + '/v3.0/search/endpointActivities', params=params, headers=headers)
            if r.json()['totalCount'] == 0:
                yield hostname


if __name__ == "__main__":
    v1 = VOne(url_base, token)
    for hostname in v1.iterate_offline(days=80):
        print(hostname)