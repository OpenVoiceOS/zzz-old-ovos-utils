from ovos_utils.messagebus import get_mycroft_bus
from ovos_utils.json_helper import merge_dict
from ovos_utils.playback.utils import check_stream, StreamStatus
from ovos_utils.parse import match_all, MatchStrategy, match_one, fuzzy_match
from ovos_utils.log import LOG
import time
from threading import Thread, Event


class CommonIPTV(Thread):
    channels = {}
    remove_threshold = 1  # stream dead N checks in a row is removed
    time_between_updates = 1  # minutes between re-checking stream status of expired {TTL} channels
    max_checks = 15  # max number of streams to check every {time_between_updates}

    def __init__(self, bus=None, *args, **kwargs):
        self.bus = bus #or get_mycroft_bus()
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
    def import_m3u8(cls, url, tags=None):
        tags = tags or []
        LOG.info(f"Importing m3u8: {url}")
        tv = M3UParser.parse_m3u8(url)
        for r in tv:
            if r.get("stream"):
                entry = {
                    "title": r["title"],
                    "duration": r["duration"],
                    "category": r.get('group-title'),
                    "logo": r.get('tvg-logo'),
                    "stream": r.get("stream"),
                    "identifier": r.get("tvg-id"),
                    "tags": tags
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


if __name__ == '__main__':
    from pprint import pprint
    from ovos_utils.playback.utils import M3UParser
    from ovos_utils.parse import match_all, MatchStrategy

    iptv = CommonIPTV()

    #iptv.setDaemon(True)

    def import_m3upt():
        url = "https://m3upt.com/iptv"

        tv = M3UParser.get_group_titles(["TV"], url)

        pt_br_tvgs = ['CNN Brasil', 'TV Câmara', 'Futura [Brazil]',
                      "AgroBrasil TV", "SBT [Brazil]", "TV Rio Preto SJRP",
                      "Retrô Cartoon"]
        pt_mz_tvgs = ["TVM", "TVM Internacional"]
        pt_cn_tvgs = ["Teledifusão de Macau (PT)"]
        cn_tvgs = ["Teledifusão de Macau (CN)"]
        pt_pt_channels = ['RTP 1', 'RTP 2', 'SIC', 'TVI', 'RTP 3',
                          'SIC Notícias', 'TVI 24', 'ARTV', 'RTP Memória',
                          'RTP Açores', 'RTP Madeira', 'RTP Internacional',
                          'RTP África', 'Porto Canal', 'TVI Internacional',
                          'SIC Internacional', 'Euronews (PT)']
        es_tvgs = ["TeleSUR", "TVE 24H", "LA 1", "LA 2",
                   "Canal Extremadura", "RT Español", "CGTN Español",
                   "DW Espanol"]
        eus_tvgs = ["ETB 1", "ETB 2", "EITB.EUS"]
        gl_tvgs = ["TV Galícia"]
        it_tvgs = ["Rai News 24"]
        en_tvgs = ["Red Bull TV", "RUSSIA TODAY (RT)", "RT America",
                   "RT UK", "RT Documentary", "CGTN", "CGTN Documentary",
                   "France 24 English", "Al Jazeera English", "Sky News",
                   "NHK WORLD JAPAN HD", "DW English"]
        fr_tvgs = ["TV5 Monde", "RT France", "CGTN Français",
                   "France 24 Français"]
        de_tvgs = ["DW Deutsch", "Deutsche Welle Deutsch+"]
        music_tvgs = ["1HD Music", "NRJ HITS", "NRG 91 TV", "Deejay TV",
                      "DELUXE MUSIC TV", "FM Italia TV",
                      "California Music Channel", "Country Music Channel",
                      "Sexy KPOP TV"]
        fashion_tvgs = ["FTV"]
        documentary_tvgs = ["CGTN Documentary", "RT Documentary"]
        news_tvgs = ["RUSSIA TODAY (RT)", "RT America", "RT UK", "CGTN",
                     "Sky News",
                     "NHK WORLD JAPAN HD", "France 24 English",
                     "Al Jazeera English", "DW English", "DW Deutsch",
                     "Deutsche Welle Deutsch+", "RT Español", "CGTN Español",
                     "DW Espanol", 'SIC Notícias',
                     'Euronews (PT)'] + fr_tvgs + it_tvgs
        cartoon_tvgs = ["Retrô Cartoon"]

        def add_entry(entry):
            entry["identifier"] = entry.get("identifier") or entry.get("title")
            if not entry["identifier"]:
                return
            if entry["title"] in news_tvgs or entry["identifier"] in news_tvgs:
                entry["tags"].append("News")
            if entry["title"] in documentary_tvgs or entry["identifier"] in \
                    documentary_tvgs:
                entry["tags"].append("Documentary")
            if entry["title"] in cartoon_tvgs or entry["identifier"] in \
                    cartoon_tvgs:
                entry["tags"].append("Cartoon")
                entry["tags"].append("Kids")
                entry["tags"].append("Animation")
            entry["skill_id"] = "skill-m3upt.jarbasskills"
            iptv.add_channel(entry)

        for r in tv:
            for t in [pt_pt_channels]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "Portuguese", "Portugal",
                                 "pt-pt"],
                        "secondary_langs": ["pt"],
                        "lang": "pt-pt"
                    }
                    add_entry(entry)
            for t in [pt_br_tvgs]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "Brazilian Portuguese",
                                 "Brazil",
                                 "pt-br", "Portuguese Ex Colonies"],
                        "secondary_langs": ["pt"],
                        "lang": "pt-br"
                    }
                    add_entry(entry)
            for t in [pt_mz_tvgs]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "Mozambique",
                                 "Portuguese Ex Colonies"],
                        "secondary_langs": ["pt"],
                        "lang": "pt-mz"  # TODO is there a real lang-code?
                    }
                    add_entry(entry)
            for t in [pt_cn_tvgs]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "Macau", "China", "Chinese",
                                 "Portuguese Ex Colonies"],
                        "secondary_langs": ["pt", "zh"],
                        "lang": "pt-zh"  # TODO is there a real lang-code?
                    }
                    add_entry(entry)
            for t in [cn_tvgs]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "Macau", "China", "Chinese",
                                 "Portuguese Ex Colonies"],
                        "secondary_langs": ["pt"],
                        "lang": "zh"  # TODO is there a real lang-code?
                    }
                    add_entry(entry)
            for t in [es_tvgs]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "Spain", "Spanish"],
                        "secondary_langs": ["es"],
                        "lang": "es-es"
                    }
                    add_entry(entry)
            for t in [eus_tvgs]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "Spain", "Spanish", "euskara",
                                 "euskera", "Basque"],
                        "secondary_langs": ["es", "es-es", "es-eus", "eus-es"],
                        "lang": "eus"
                    }
                    add_entry(entry)
            for t in [gl_tvgs]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "Spain", "Spanish", "Galicia",
                                 "Galician"],
                        "secondary_langs": ["es", "es-es", "es-gl", "gl-es",
                                            "pt"],
                        "lang": "gl"
                    }
                    add_entry(entry)
            for t in [en_tvgs]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "English"],
                        "secondary_langs": [],
                        "lang": "en"
                    }
                    add_entry(entry)
            for t in [it_tvgs]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "Italy", "Italian"],
                        "secondary_langs": ["it"],
                        "lang": "it-it"
                    }
                    add_entry(entry)
            for t in [de_tvgs]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "German", "Germany",
                                 "Deutsche"],
                        "secondary_langs": ["de"],
                        "lang": "de-de"
                    }
                    add_entry(entry)
            for t in [fr_tvgs]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "French", "France"],
                        "secondary_langs": ["fr"],
                        "lang": "fr-fr"
                    }
                    add_entry(entry)
            for t in [music_tvgs]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "Music", "Music Channel"]
                    }
                    add_entry(entry)
            for t in [fashion_tvgs]:
                if r["title"] in t or r["tvg-id"] in t:
                    entry = {
                        "title": r["title"],
                        "duration": r["duration"],
                        "category": r.get('group-title'),
                        "logo": r.get('tvg-logo'),
                        "stream": r.get("stream"),
                        "identifier": r.get("tvg-id"),
                        "tags": ["TV", "IPTV", "Fashion"]
                    }
                    add_entry(entry)


    music = "https://raw.githubusercontent.com/Free-IPTV/Countries/master/YZ001_MUSIC.m3u"
    usa = "https://raw.githubusercontent.com/Free-IPTV/Countries/master/US01_USA.m3u"
    uk = "https://raw.githubusercontent.com/Free-IPTV/Countries/master/UK01_UNITED_KINGDOM.m3u"
    pt = "https://raw.githubusercontent.com/Free-IPTV/Countries/master/PT01_PORTUGAL.m3u"
    es = "https://raw.githubusercontent.com/Free-IPTV/Countries/master/ES01_SPAIN.m3u"
    br = "https://raw.githubusercontent.com/Free-IPTV/Countries/master/BR01_BRAZIL.m3u"

    iptv.import_m3u8(music, tags=["Music"])
    #iptv.import_m3u8(usa, tags=["USA", "English", "America"])
    #iptv.import_m3u8(uk, tags=["UK", "English", "England", "British"])
    #iptv.import_m3u8(pt, tags=["Portugal", "Portuguese"])
    #iptv.import_m3u8(es, tags=["Spain", "Spanish"])
    #iptv.import_m3u8(br, tags=["Brazil", "Brazilian"])

    #import_m3upt()

    iptv.start()

    exit()
    #time.sleep(30)
    #iptv.stop()

    results = iptv.get_channels()

    results = iptv.search("music")

    import_m3upt()
    results = iptv.filter_by_language("pt")

