import json


class PollConfig:
    def __init__(self, rule_id=None, rule_value=None):
        self.id = rule_id
        self.value = rule_value

    def __str__(self):
        return json.dumps(self, default=lambda x: x.__dict__)


class PollConfigKey:
    def __init__(self, rule_id=None):
        self.id = rule_id

    def __str__(self):
        return json.dumps(self, default=lambda x: x.__dict__)


class PollResponse:
    def __init__(self, sender_ip=None, session_name=None, what_went_well=None, what_went_wrong=None):
        #self.id = response_id
        self.sender_ip = sender_ip
        self.session_name = session_name
        self.what_went_well = what_went_well
        self.what_went_wrong = what_went_wrong

    def __str__(self):
        return json.dumps(self, default=lambda x: x.__dict__)


class PollResponseKey:
    def __init__(self, sender_ip=None, session_name=None):
        self.sender_ip = sender_ip
        self.session_name = session_name

    def __str__(self):
        return json.dumps(self, default=lambda x: x.__dict__)

