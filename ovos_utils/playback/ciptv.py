from ovos_utils.messagebus import get_mycroft_bus
from ovos_utils.json_helper import merge_dict
from ovos_utils.playback.utils import check_stream, StreamStatus
from ovos_utils.parse import match_all, MatchStrategy, match_one, fuzzy_match
from ovos_utils.log import LOG
from ovos_utils.playback.utils import M3UParser
import time
from threading import Thread, Event


class CommonIPTV(Thread):
    channels = {}
    remove_threshold = 1  # stream dead N checks in a row is removed
    time_between_updates = 1  # minutes between re-checking stream status of expired {TTL} channels
    max_checks = 15  # max number of streams to check every {time_between_updates}
    _duplicates = {}  # url:[idx] uniquely identifying duplicate channels

    def __init__(self, bus=None, *args, **kwargs):
        self.bus = bus  # or get_mycroft_bus()
        self.stop_event = Event()
        self._last_check = time.time()
        super(CommonIPTV, self).__init__(*args, **kwargs)

    @classmethod
    def add_channel(cls, channel):
        channel["expires"] = 0
        channel["status"] = StreamStatus.UNKNOWN
        channel["_dead_counter"] = 0
        channel_id = channel.get("identifier") or channel.get("title")
        LOG.info(f"Adding channel: {channel_id}")
        cls.channels[channel_id] = channel

    @classmethod
    def update_channel(cls, channel):
        channel_id = cls.find_channel_id(channel)
        cls.channels[channel_id] = merge_dict(cls.channels[channel_id],
                                              channel)

    @classmethod
    def get_channel_status(cls, channel):
        if isinstance(channel, str):
            channel = cls.find_channel(channel)
        stream = channel.get("stream")
        if not stream:
            # TODO allow callback mode to ask stream provider
            # - we have a message type in payload instead of stream
            # - we send that bus message and wait reply with actual stream
            # - allows searching without extracting (slow), eg, youtube
            raise KeyError("channel has no associated stream")
        return check_stream(stream, timeout=5)

    @classmethod
    def find_channel(cls, key):
        if key in cls.channels:
            return cls.channels[key]
        for idx, ch in cls.channels.items():
            if ch.get("id") == key:
                return ch
            elif ch.get("identifier") == key:
                return ch
            elif ch.get("uri") == key:
                return ch
            elif ch.get("stream") == key:
                return ch
            elif ch.get("url") == key:
                return ch
            elif ch.get("title") == key:
                return ch

    @classmethod
    def find_channel_id(cls, key):
        if key in cls.channels:
            return key
        for idx, ch in cls.channels.items():
            if ch.get("id") == key:
                return idx
            elif ch.get("identifier") == key:
                return idx
            elif ch.get("uri") == key:
                return idx
            elif ch.get("stream") == key:
                return idx
            elif ch.get("url") == key:
                return idx
            elif ch.get("title") == key:
                return idx

    @classmethod
    def delete_channel(cls, key):
        if key in cls.channels:
            cls.channels.pop(key)
            return
        for idx, ch in cls.channels.items():
            if ch.get("id") == key:
                cls.channels.pop(key)
                return
            elif ch.get("identifier") == key:
                cls.channels.pop(key)
                return
            elif ch.get("uri") == key:
                cls.channels.pop(key)
                return
            elif ch.get("stream") == key:
                cls.channels.pop(key)
                return
            elif ch.get("url") == key:
                cls.channels.pop(key)
                return
            elif ch.get("title") == key:
                cls.channels.pop(key)
                return

    @classmethod
    def prune_dead_streams(cls, ttl=60):
        """ remove dead streams from channel list
        set stream status as OK for ttl minutes"""
        for idx, ch in dict(cls.channels).items():
            if cls.channels[idx]["status"] != StreamStatus.OK:
                cls.channels[idx]["status"] = cls.get_channel_status(ch)
                cls.channels[idx]["expires"] = time.time() + ttl * 60
                if cls.channels[idx]["status"] == StreamStatus.OK:
                    cls.channels[idx]["_dead_counter"] = 0
                else:
                    cls.channels[idx]["_dead_counter"] += 1
                    if cls.channels[idx]["_dead_counter"] >= \
                            cls.remove_threshold:
                        LOG.info(f"Removing dead stream: {idx}")
                        cls.delete_channel(idx)

    @classmethod
    def update_stream_status(cls, ttl=120):
        # order channels by expiration date
        channels = sorted([(idx, ch)
                           for idx, ch in dict(cls.channels).items()],
                          key=lambda k: k[1]["expires"])
        # update N channels status
        for idx, ch in channels[:cls.max_checks]:
            if cls.channels[idx]["expires"] - time.time() < 0:
                cls.channels[idx]["status"] = cls.get_channel_status(ch)
                cls.channels[idx]["expires"] = time.time() + ttl * 60
                LOG.info(f'{idx} stream status: {cls.channels[idx]["status"]}')

    @classmethod
    def find_duplicate_streams(cls):
        """ detect streams that are duplicated by several skills """
        urls = [(ix, ch["stream"]) for ix, ch in cls.channels.items()]
        for ix, prev_url in urls:
            for idx, ch in dict(cls.channels).items():
                if idx == ix:
                    continue
                url = ch.get("stream")
                if url == prev_url:
                    if prev_url not in cls._duplicates:
                        LOG.info(f"Duplicate channel detected {idx}")
                        cls._duplicates[prev_url] = [idx]
                    elif idx not in cls._duplicates[prev_url]:
                        cls._duplicates[prev_url].append(idx)

    @classmethod
    def import_m3u8(cls, url, tags=None):
        tags = tags or []

        LOG.info(f"Importing m3u8: {url}")
        tv = M3UParser.parse_m3u8(url)
        for r in tv:
            default_tags = ["TV", "IPTV"] + [r['group-title']]
            if r.get("stream"):
                entry = {
                    "title": r["title"],
                    "duration": r["duration"],
                    "category": r['group-title'],
                    "logo": r.get('tvg-logo'),
                    "stream": r.get("stream"),
                    "identifier": r.get("tvg-id"),
                    "tags": tags + default_tags,
                }
                if r.get("category"):
                    entry["tags"].append(r["category"])
                cls.add_channel(entry)

    # iptv functionality
    def get_channels(self, filter_dead=False):
        if filter_dead:
            return [ch for idx, ch in self.channels.items()
                    if ch["status"] == StreamStatus.OK]
        return [ch for idx, ch in self.channels.items()]

    def get_duplicated_channels(self):
        duplicates = []
        for url, channels in self._duplicates.items():
            duplicates.append(channels)
        return duplicates

    def search(self, query, lang=None,
               strategy=MatchStrategy.TOKEN_SORT_RATIO, filter_dead=False,
               minconf=50):
        query = query.lower().strip()
        if lang:
            channels = self.filter_by_language(lang)
        else:
            channels = self.get_channels()
        matches = []
        for ch in channels:
            # score name match
            names = ch.get("aliases") or []
            names.append(ch.get("title") or ch["identifier"])
            names = [_.lower().strip() for _ in names]
            best_name, name_score = match_one(query, names, strategy=strategy)
            name_score = name_score * 50
            if query in best_name:
                name_score += 30

            # score tag matches
            tags = ch.get("tags", [])
            tags = [_.lower().strip() for _ in tags]
            tag_scores = match_all(query, tags, strategy=strategy)[:5]
            tag_score = sum([0.5 * t[1] for t in tag_scores]) / len(
                tag_scores) * 100
            if query in tags:
                tag_score += 30

            score = min(tag_score + name_score, 100)
            if score >= minconf:
                if not filter_dead:
                    matches.append((ch, score))
                elif ch["status"] == StreamStatus.OK:
                    matches.append((ch, score))

        return sorted(matches, key=lambda k: k[1], reverse=True)

    def filter_by_language(self, lang):
        return [c for c in self.get_channels() if
                c.get("lang") == lang or
                c.get("lang", "").split("-")[0] == lang or
                lang in c.get("secondary_langs", [])]

    # event loop
    def run(self) -> None:
        self.stop_event.clear()
        while not self.stop_event.is_set():

            # remove any dead streams
            self.prune_dead_streams()

            # take note of duplicated channels
            self.find_duplicate_streams()

            time.sleep(5)

            # confirm working status of existing streams
            if time.time() - self._last_check > self.time_between_updates * 60:
                self.update_stream_status()
                self._last_check = time.time()

    def stop(self):
        self.stop_event.set()

    # bus api
    def handle_register_channel(self, message):
        channel = message.data
        self.add_channel(channel)

    def handle_update_channel(self, message):
        # validate stream status if needed
        if message.data.get("validate_stream"):
            if self.get_channel_status(message.data) != StreamStatus.OK:
                # abort update
                return
            message.data.pop("validate_stream")
        idx = self.find_channel_id(message.data)
        if idx:
            self.update_channel(message.data)
        else:
            self.handle_register_channel(message)


