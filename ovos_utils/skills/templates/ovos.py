from ovos_utils.waiting_for_mycroft.base_skill import MycroftSkill, FallbackSkill


class OVOSSkill(MycroftSkill):
    """ monkey patched mycroft skill """


class OVOSFallbackSkill(FallbackSkill):
    """ monkey patched mycroft fallback skill """

