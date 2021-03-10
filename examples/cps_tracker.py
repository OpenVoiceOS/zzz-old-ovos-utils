from ovos_utils import wait_for_exit_signal
from ovos_utils.playback.cps import CPSTracker


g = CPSTracker()

wait_for_exit_signal()
