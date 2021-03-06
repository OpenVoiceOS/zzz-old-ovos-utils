from ovos_utils.playback.youtube import get_youtube_metadata, is_youtube
import requests


def get_duration_from_url(url):
    """ return stream duration in milliseconds """
    if not url:
        return 0
    if is_youtube(url):
        data = get_youtube_metadata(url)
        dur = data.get("length", 0)
    else:
        headers = requests.head(url).headers
        #print(headers)
        #dur = int(headers.get("Content-Length", 0))
        dur = 0
    return dur


def get_title_from_url(url):
    """ return stream duration in milliseconds """
    if url and is_youtube(url):
        data = get_youtube_metadata(url)
        return data.get("title")
    return url
