from ovos_utils.skills.settings import PrivateSettings


with PrivateSettings("testskill.jarbasai") as settings:
    print(settings.path)  # ~/.cache/json_database/testskill.jarbasai.json
    settings["key"] = "value"
    # auto saved when leaving "with" context
    # you can also manually call settings.store() if not using "with" context