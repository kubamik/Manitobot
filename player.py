from permissions import can_refuse


class Player:

    def __init__(self, member, role):
        self.member = member
        self.role = role
        self.active = False
        self.sleeped = False
        self.protected = False
        self.killing_protected = False
        self.role_class = None

    def can_refuse(self):
        return self.role in can_refuse

    def new_day(self):
        self.sleeped = False
        self.protected = False
        self.killing_protected = False
