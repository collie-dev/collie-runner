import requests

from colint import secret


def delete_annotation(annotation_id):
    url = f"{secret.GRAFANA_HOST}/api/annotations/{annotation_id}"
    res = requests.delete(url, headers=secret.AUTH_HEADERS)
    res.raise_for_status()
    print(res.text)
    return


def delete_all_annotation_by_dashboard_id(dashboard_id):
    url = f"{secret.GRAFANA_HOST}/api/annotations?from=1601389423278&to=1691418702639&limit=10000&dashboardId={dashboard_id}"
    res = requests.get(url, headers=secret.AUTH_HEADERS)
    res.raise_for_status()

    data = res.json()
    for annotation in data:
        delete_annotation(annotation["id"])


# for i in range(270, 284):
#     delete_annotation(i)
#     print(i)

delete_all_annotation_by_dashboard_id(17)
