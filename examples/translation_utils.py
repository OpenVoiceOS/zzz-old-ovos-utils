from ovos_utils.lang import detect_lang, translate_text

# detecting language
assert detect_lang("olá eu chamo-me joaquim") == "pt"

assert detect_lang("olá eu chamo-me joaquim", return_dict=True) == \
       {'confidence': 0.9999939001351439, 'language': 'pt'}

assert detect_lang("hello world") == "en"

assert detect_lang(
    "This piece of text is in English. Този текст е на Български.",
    return_dict=True) == {'confidence': 0.28571342657428966, 'language': 'en'}

# translating text

## source lang will be auto detected using utils above
## default target language is english
assert translate_text("olá eu chamo-me joaquim") == "Hello I call myself joaquim"

## you should specify source lang whenever possible to save 1 api call
assert translate_text("olá eu chamo-me joaquim", source_lang="pt") == "Hello I call myself joaquim"