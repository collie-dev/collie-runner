# http://18.183.82.139:3000/api/datasources/proxy/2/api/v1/label/__name__/values

import requests

from colint import secret

res = requests.get(f"{secret.GRAFANA_HOST}/api/datasources/proxy/3/api/v1/label/__name__/values",
                   headers=secret.AUTH_HEADERS)


metrics = res.json()["data"]
buckets = {}
for metric in metrics:
    namespace = metric.split("_")[0]
    if namespace not in buckets:
        buckets[namespace] = 0
    buckets[namespace] += 1


print("metric_count:", len(metrics))
print({k: v for k, v in sorted(buckets.items(), key=lambda item: item[1], reverse=True)})