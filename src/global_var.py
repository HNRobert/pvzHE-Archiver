# The GlobalsVar class is used to store global variables.
class GlobalsVar:
    def __init__(self):
        self.gvar = {
            "n_s": False,
            "has_new_save": False,
            "rescan_savings": False,
            "game_exist": False,
            'note_data': {},
            'continue_scanning': True,
        }

    def get(self, key):
        return self.gvar[key]

    def set(self, key, value):
        self.gvar[key] = value
        return True


gvar = GlobalsVar()
