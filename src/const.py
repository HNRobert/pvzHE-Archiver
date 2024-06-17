import os

HE_ARCHIVER_DATA_PATH = "C:\\ProgramData\\pvzHEArchiver"
HE_ARCHIVER_DATA = os.path.join(HE_ARCHIVER_DATA_PATH, "data.json")
HE_ARCHIVER_ICON = os.path.join(HE_ARCHIVER_DATA_PATH, "icon.ico")
HE_ARCHIVER_GAME_DATA_PATH = os.path.join(HE_ARCHIVER_DATA_PATH, "game_data")

HE_DATA_PATH = "C:\\ProgramData\\PopCap Games\\PlantsVsZombies\\pvzHE\\yourdata"
USERS_DAT = os.path.join(HE_DATA_PATH, "users.dat")

GAME_DAT_PATTERN = r"game(\d+)_(\d+)\.dat"
ARCHED_DAT_PATTERN = r"(\d+)-(\d+)-(\d+)-(\d+)\.dat"
