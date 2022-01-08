import json
import time

import pandas as pd
import requests

from colint import secret
from urllib.parse import quote

from colint.detector.k import bocp, robust_stat
from colint.detector.l import luminol_detector
from colint.detector.models import ChangePoint


class Panel:
    id: str
    expr: str

    def __init__(self, expr, id, args):
        self.expr = expr
        self.id = id
        self.args = args

    def panel_to_data(self, start, end, step=30):
        query = f"{self.expr}".replace("$tidb_cluster", secret.TIDB_CLUSTER).replace("$instance",
                                                                                     secret.PD_INSTANCE).strip()
        encode_query = quote(query, safe="()")
        params = f"query={encode_query}&start={start}&end={end}&step={step}"
        url = f"{secret.GRAFANA_HOST}/api/datasources/proxy/{secret.DATASOURCE_ID}/api/v1/query_range?" + params
        req = requests.get(url, headers=secret.AUTH_HEADERS)
        req.raise_for_status()
        return req.json()

    def metric_value_to_df(self, values):
        df = pd.DataFrame(values, columns=['time', "value"])
        # to nanosec
        df['time'] = pd.to_numeric(df['time']).mul(1000000000)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        return df

    def metric_to_kpis(self, metrics_data):
        metrics = metrics_data["data"]["result"]
        kpis = []
        for metric in metrics:
            kpi = {"panel_id": self.id}
            kpi["name"] = self.expr.split("{")[0].split("(")[-1]
            if "legendFormat" in self.args:
                kpi["name"] += "-" + self.args["legendFormat"]
            if "metric" in metric:
                kpi["name"] += "-".join(metric["metric"].values())

            kpi["df"] = self.metric_value_to_df(metric["values"])
            kpis.append(kpi)
        return kpis


def decode_panels(panel):
    if "panels" in panel:
        for p in panel["panels"]:
            decode_panels(p)
    if "type" in panel:
        type = panel["type"]
        if type != "row" and type != "graph":
            return

    if "targets" in panel:
        for t in panel["targets"]:
            if "format" in t and t["format"] == "time_series":
                if "hide" in t and not t["hide"]:
                    return
                panels.append(Panel(t["expr"], panel["id"], t))


def create_annotation(dashboard_id, panel_id, text, time_point):
    url = f"{secret.GRAFANA_HOST}/api/annotations"
    res = requests.post(url, headers=secret.AUTH_HEADERS, json={
        "dashboardId": dashboard_id,
        "isRegion": False,
        "panelId": panel_id,
        "tags": [],
        "text": text,
        "time": time_point,
        "timeEnd": 0,
    })
    res.raise_for_status()
    # print("created", res.text)

def panel_detector(panel: Panel, set_grafana=False):
    prometheus_data = panel.panel_to_data(1641563854, 1641574654)
    kpis = panel.metric_to_kpis(prometheus_data)
    results = {}

    print("Start detector", time.time())

    for kpi in kpis:
        if kpi["df"].size == 0:
            continue

        change_points = robust_stat(kpi["df"])
        result = {
            "df": kpi["df"],
            "change_points": change_points
        }
        if set_grafana:
            for p in change_points:
                create_annotation(17, kpi["panel_id"], f"robust_stat name:{kpi['name']}  confidence:{p.score}",
                                  int(p.start / 1000000))

        change_points = luminol_detector(kpi["df"])
        result["change_points"] += change_points
        if set_grafana:
            for p in change_points:
                create_annotation(17, kpi["panel_id"], f"luminol name:{kpi['name']}  confidence:{p.score}",
                                  int(p.start / 1000000))

        results[kpi["name"]] = result
    return results


url = f"{secret.GRAFANA_HOST}/api/dashboards/uid/{secret.DASHBOARD_KEY}"
req = requests.get(url, headers=secret.AUTH_HEADERS)
data = req.json()
panels = []

# for p in data["dashboard"]["panels"]:
#     decode_panels(p)

decode_panels(data["dashboard"])


metrics = []
for panel in panels:
    res = panel_detector(panel, set_grafana=True)
    for key, value in res.items():
        cp = []
        for i in value["change_points"]:
            cp.append({"start": i.start, "end": i.end})

        value["df"]["time"] = value["df"]["time"].div(1000000)
        metrics.append({
            "name": key,
            "min": float(value['df']["value"].min()),
            "max": float(value['df']["value"].max()),
            "values":value["df"].values.tolist(),
            "change_point": cp
        })

with open("/tmp/data.json", "w") as f:
    data = json.dumps(metrics).replace("NaN", "null")
    f.write(data)