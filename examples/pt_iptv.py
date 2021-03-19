from pprint import pprint
from ovos_utils.playback.utils import M3UParser
from ovos_utils.parse import match_all, MatchStrategy
from ovos_utils.playback.ciptv import CommonIPTV


iptv = CommonIPTV()
# iptv.setDaemon(True)

music = "https://raw.githubusercontent.com/Free-IPTV/Countries/master/YZ001_MUSIC.m3u"
usa = "https://raw.githubusercontent.com/Free-IPTV/Countries/master/US01_USA.m3u"
uk = "https://raw.githubusercontent.com/Free-IPTV/Countries/master/UK01_UNITED_KINGDOM.m3u"
pt = "https://raw.githubusercontent.com/Free-IPTV/Countries/master/PT01_PORTUGAL.m3u"
es = "https://raw.githubusercontent.com/Free-IPTV/Countries/master/ES01_SPAIN.m3u"
br = "https://raw.githubusercontent.com/Free-IPTV/Countries/master/BR01_BRAZIL.m3u"

# iptv.import_m3u8(music, tags=["Music"])
# iptv.import_m3u8(usa, tags=["USA", "English", "America"])
# iptv.import_m3u8(uk, tags=["UK", "English", "England", "British"])
iptv.import_m3u8(pt, tags=["Portugal", "Portuguese"])
iptv.import_m3u8(es, tags=["Spain", "Spanish"])
iptv.import_m3u8(br, tags=["Brazil", "Brazilian"])


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


def import_ptiptv():
    url = "https://ptiptv.tk/lista.m3u8"
    pt_tvgs = ['SIC', 'TVI', 'SICN', 'TVI24', 'ARTV', 'TVI Reality',
               'PORTO', 'TVI Internacional', 'Zig Zag',
               '#EstudoEmCasa']
    fashion_tvgs = ['Fashion TV Paris', 'FTV',
                    'Fashion TV Midnight Secrets']
    es_tvgs = ['TVE24HD', 'TVE 🇪🇸', 'TVGAL']
    fr_tvgs = ['TV5', 'FR24F']
    it_tvgs = ['RAINEWS']
    en_tvgs = ['BLOOM', 'SKYN', 'FR24I', 'DWTVHD', 'ALJAZ', 'RUSSTHD',
               'NHKHD', 'CGTN', 'CGTNDHD']
    de_tvgs = ['DWTVA']

    def add_entry(entry):
        entry["identifier"] = entry.get("identifier") or \
                              entry.get("tvg-id") or \
                              entry.get("title")
        if not entry["identifier"]:
            return
        entry["skill_id"] = "skill-ptiptv.jarbasskills"
        iptv.add_channel(entry)

    for r in M3UParser.parse_m3u8(url):
        if r.get("radio"):
            continue
        lang = None
        if r["title"] in pt_tvgs or r["tvg-id"] in pt_tvgs:
            lang = "pt-pt"
        if r["title"] in es_tvgs or r["tvg-id"] in es_tvgs:
            lang = "es"
        if r["title"] in en_tvgs or r["tvg-id"] in en_tvgs:
            lang = "en"
        if r["title"] in it_tvgs or r["tvg-id"] in it_tvgs:
            lang = "it"
        if r["title"] in fr_tvgs or r["tvg-id"] in fr_tvgs:
            lang = "fr"
        if r["title"] in de_tvgs or r["tvg-id"] in de_tvgs:
            lang = "de"
        entry = {
            "title": r["title"],
            "duration": r["duration"],
            "category": r.get('group-title'),
            "logo": r.get('tvg-logo'),
            "stream": r.get("stream"),
            "identifier": r.get("tvg-id"),
            "lang": lang,
            "tags": ["TV", "IPTV"] + [r['group-title']]
        }
        add_entry(entry)


import_ptiptv()
import_m3upt()
iptv.import_m3u8(pt, tags=["Portugal", "Portuguese"])
iptv.import_m3u8(es, tags=["Spain", "Spanish"])
iptv.import_m3u8(br, tags=["Brazil", "Brazilian"])

iptv.find_duplicate_streams()

dups = iptv.get_duplicated_channels()
pprint(dups)

exit()
iptv.start()

exit()
# time.sleep(30)
# iptv.stop()

results = iptv.get_channels()

results = iptv.search("music")

import_m3upt()
results = iptv.filter_by_language("pt")
