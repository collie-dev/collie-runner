import luminol
import luminol.anomaly_detector
import luminol.correlator
from luminol.modules.time_series import TimeSeries

from colint.detector.models import ChangePoint


def luminol_detector(df):
    ts = TimeSeries({})
    ts.timestamps = df["time"]
    ts.values = df["value"]
    detector = luminol.anomaly_detector.AnomalyDetector(ts)
    anomalies = detector.get_anomalies()
    if anomalies:
        return [ChangePoint(c.start_timestamp, c.end_timestamp, c.anomaly_score) for c in anomalies]
    return []
