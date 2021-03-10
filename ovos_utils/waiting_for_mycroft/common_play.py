# Copyright 2018 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from inspect import signature
from abc import abstractmethod
from enum import IntEnum
from ovos_utils.waiting_for_mycroft.base_skill import MycroftSkill
from ovos_utils.playback import CPSMatchType, CPSTrackStatus
try:
    from mycroft.skills.common_play_skill import CommonPlaySkill as _CommonPlaySkill
except ImportError:
    import sys
    from ovos_utils.log import LOG
    from ovos_utils import get_mycroft_root
    MYCROFT_ROOT_PATH = get_mycroft_root()
    if MYCROFT_ROOT_PATH is not None:
        sys.path.append(MYCROFT_ROOT_PATH)
        from mycroft.skills.common_play_skill import CommonPlaySkill as _CommonPlaySkill
    else:
        LOG.error("Could not find mycroft root path")
        raise ImportError


# implementation of
# https://github.com/MycroftAI/mycroft-core/pull/2660
class CPSMatchLevel(IntEnum):
    EXACT = 1
    MULTI_KEY = 2
    TITLE = 3
    ARTIST = 4
    CATEGORY = 5
    GENERIC = 6


class CommonPlaySkill(MycroftSkill, _CommonPlaySkill):
    """ To integrate with the common play infrastructure of Mycroft
    skills should use this base class and override the two methods
    `CPS_match_query_phrase` (for checking if the skill can play the
    utterance) and `CPS_start` for launching the media.

    The class makes the skill available to queries from the
    mycroft-playback-control skill and no special vocab for starting playback
    is needed.
    """
    def __init__(self, name=None, bus=None):
        super().__init__(name, bus)

        self.supported_media = [CPSMatchType.GENERIC, CPSMatchType.MUSIC]
        # NOTE: derived skills will likely want to override this list,
        # for backwards compatibility MUSIC is supported as a default

    def __handle_play_query(self, message):
        """Query skill if it can start playback from given phrase."""
        search_phrase = message.data["phrase"]
        media_type = message.data.get("media_type", CPSMatchType.GENERIC)

        if media_type not in self.supported_media:
            return

        # First, notify the requestor that we are attempting to handle
        # (this extends a timeout while this skill looks for a match)
        self.bus.emit(message.response({"phrase": search_phrase,
                                        "skill_id": self.skill_id,
                                        "searching": True}))

        # Now invoke the CPS handler to let the skill perform its search
        if len(signature(self.CPS_match_query_phrase).parameters) == 2:
            result = self.CPS_match_query_phrase(search_phrase, media_type)
        else:
            # needed for old skills which are not expecting media_type
            # TODO remove in next major release
            result = self.CPS_match_query_phrase(search_phrase)

        if result:
            match = result[0]
            level = result[1]
            callback = result[2] if len(result) > 2 else None
            confidence = self.__calc_confidence(match, search_phrase, level)
            self.bus.emit(message.response({"phrase": search_phrase,
                                            "skill_id": self.skill_id,
                                            "callback_data": callback,
                                            "service_name": self.spoken_name,
                                            "conf": confidence}))
        else:
            # Signal we are done (can't handle it)
            self.bus.emit(message.response({"phrase": search_phrase,
                                            "skill_id": self.skill_id,
                                            "searching": False}))

    def __handle_play_start(self, message):
        """Bus handler for starting playback using the skill."""
        if message.data["skill_id"] != self.skill_id:
            # Not for this skill!
            return
        phrase = message.data["phrase"]
        data = message.data.get("callback_data")

        # Stop any currently playing audio
        if self.audioservice.is_playing and \
                message.data.get("stop_audio", True):
            # "stop_audio" is used by playback control, it avoids calling stop
            # if query was interpreted as a "resume" command
            self.audioservice.stop()

            self.bus.emit(message.forward("mycroft.stop"))

        # Save for CPS_play() later, e.g. if phrase includes modifiers like
        # "... on the chromecast"
        self.play_service_string = phrase

        # Invoke derived class to provide playback data
        self.CPS_start(phrase, data)

    ######################################################################
    # Abstract methods
    # All of the following must be implemented by a skill that wants to
    # act as a CommonPlay Skill
    @abstractmethod
    def CPS_match_query_phrase(self, phrase, media_type):
        """Analyze phrase to see if it is a play-able phrase with this skill.

        Arguments:
            phrase (str): User phrase uttered after "Play", e.g. "some music"

        Returns:
            (match, CPSMatchLevel[, callback_data]) or None: Tuple containing
                 a string with the appropriate matching phrase, the PlayMatch
                 type, and optionally data to return in the callback if the
                 match is selected.
        """
        # Derived classes must implement this, e.g.
        #
        # if phrase in ["Zoosh"]:
        #     return ("Zoosh", CPSMatchLevel.Generic, {"hint": "music"})
        # or:
        # zoosh_song = find_zoosh(phrase)
        # if zoosh_song and "Zoosh" in phrase:
        #     # "play Happy Birthday in Zoosh"
        #     return ("Zoosh", CPSMatchLevel.MULTI_KEY, {"song": zoosh_song})
        # elif zoosh_song:
        #     # "play Happy Birthday"
        #     return ("Zoosh", CPSMatchLevel.TITLE, {"song": zoosh_song})
        # elif "Zoosh" in phrase
        #     # "play Zoosh"
        #     return ("Zoosh", CPSMatchLevel.GENERIC, {"cmd": "random"})
        return None
