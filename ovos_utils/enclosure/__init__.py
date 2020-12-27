from ovos_utils.system import get_platform_fingerprint, MycroftRootLocations
from enum import Enum


class MycroftEnclosures(str, Enum):
    PICROFT = "picroft"
    BIGSCREEN = "mycroft_mark_2"  # TODO handle bigscreen
    OVOS = "OpenVoiceOS"
    OLD_MARK1 = "mycroft_mark_1(old)"
    MARK1 = "mycroft_mark_1"
    MARK2 = "mycroft_mark_2"
    OTHER = "unknown"


def enclosure2rootdir(enclosure=None):
    enclosure = enclosure or detect_enclosure()
    if enclosure == MycroftEnclosures.OLD_MARK1:
        return MycroftRootLocations.OLD_MARK1
    elif enclosure == MycroftEnclosures.MARK1:
        return MycroftRootLocations.MARK1
    elif enclosure == MycroftEnclosures.MARK2:
        return MycroftRootLocations.MARK2
    elif enclosure == MycroftEnclosures.PICROFT:
        return MycroftRootLocations.PICROFT
    elif enclosure == MycroftEnclosures.OVOS:
        return MycroftRootLocations.OVOS
    elif enclosure == MycroftEnclosures.BIGSCREEN:
        return MycroftRootLocations.BIGSCREEN
    raise EnvironmentError


def detect_enclosure():
    # TODO very naive check, improve this
    # use db of reference fingerprints
    fingerprint = get_platform_fingerprint()
    if fingerprint["enclosure"] == "OpenVoiceOS":
        return MycroftEnclosures.OVOS
    elif fingerprint["enclosure"] == "mycroft_mark_1":
        if fingerprint["mycroft_core_location"] == MycroftRootLocations.MARK1 or \
                fingerprint["mycroft_core_location"] == MycroftRootLocations.OLD_MARK1:
            return MycroftEnclosures.OLD_MARK1
        return MycroftEnclosures.MARK1
    elif fingerprint["enclosure"] == "mycroft_mark_2":
        # TODO bigscreen also reports this...
        return MycroftEnclosures.MARK2
    elif fingerprint["enclosure"] == "picroft":
        return MycroftEnclosures.PICROFT

    return "unknown"




