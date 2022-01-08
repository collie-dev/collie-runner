from kats.detectors.robust_stat_detection import RobustStatDetector
from kats.detectors.bocpd import BOCPDetector, BOCPDModelType

from kats.consts import TimeSeriesData

from colint.detector.models import ChangePoint


def robust_stat(df):
    tsd = TimeSeriesData(df)
    detector = RobustStatDetector(tsd)
    points = detector.detector()
    return to_changepoint(points)


def bocp(df):
    tsd = TimeSeriesData(df)
    # Initialize the detector
    detector = BOCPDetector(tsd)
    points = detector.detector(
        model=BOCPDModelType.NORMAL_KNOWN_MODEL  # this is the default choice
    )
    return to_changepoint(points)


def to_changepoint(points):
    return [ChangePoint(int(p[0].start_time), int(p[0].end_time), p[0].confidence) for p in points]
