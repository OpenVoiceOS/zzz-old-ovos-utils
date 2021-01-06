from ovos_utils.system import is_installed, has_screen
from ovos_utils.messagebus import wait_for_reply


def can_display():
    return has_screen()


def is_gui_installed():
    return is_installed("mycroft-gui-app")


def is_gui_connected(bus=None):
    # bus api for https://github.com/MycroftAI/mycroft-core/pull/2682
    # send "gui.status.request"
    # receive "gui.status.request.response"
    response = wait_for_reply("gui.status.request",
                              "gui.status.request.response", bus=bus)
    if response:
        return response.data["connected"]
    return False
