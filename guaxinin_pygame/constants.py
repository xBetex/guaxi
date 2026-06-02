"""
Constants and color definitions for Guaxinim game
"""
import math

# Screen settings
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

# Themes for different times of day
THEMES = {
    "manha": {
        "sky1": (116, 185, 255),
        "sky2": (129, 236, 236),
        "sky3": (255, 234, 167),
        "mountain": (130, 115, 151),
        "mountain_light": (162, 155, 254)
    },
    "dia": {
        "sky1": (9, 132, 227),
        "sky2": (116, 185, 255),
        "sky3": (129, 236, 236),
        "mountain": (74, 91, 99),
        "mountain_light": (99, 110, 114)
    },
    "tarde": {
        "sky1": (108, 92, 231),
        "sky2": (232, 67, 147),
        "sky3": (253, 203, 110),
        "mountain": (27, 27, 47),
        "mountain_light": (45, 52, 54)
    },
    "noite": {
        "sky1": (0, 0, 0),
        "sky2": (30, 39, 46),
        "sky3": (15, 20, 35),
        "mountain": (10, 10, 15),
        "mountain_light": (30, 39, 46)
    }
}

# Season colors - FIXED: Proper seasonal grass colors
SEASON_COLORS = {
    "spring": {
        "grass1": (85, 239, 196),
        "grass2": (0, 184, 148),
        "leaf_main": (253, 121, 168),
        "leaf_normal": (232, 67, 147),
        "leaf_edge": (214, 48, 49)
    },
    "summer": {
        "grass1": (120, 224, 143),
        "grass2": (56, 173, 169),
        "leaf_main": (46, 204, 113),
        "leaf_normal": (39, 174, 96),
        "leaf_edge": (30, 132, 73)
    },
    "autumn": {
        "grass1": (229, 142, 38),
        "grass2": (183, 21, 64),
        "leaf_main": (243, 156, 18),
        "leaf_normal": (211, 84, 0),
        "leaf_edge": (230, 126, 34)
    },
    "winter": {
        "grass1": (223, 230, 233),
        "grass2": (178, 190, 195),
        "leaf_main": (236, 240, 241),
        "leaf_normal": (189, 195, 199),
        "leaf_edge": (149, 165, 166)
    }
}

# Base sprite colors
BASE_COLORS = {
    "K": (30, 39, 46),      # Dark bark
    "B": (131, 76, 50),     # Brown trunk
    "D": (92, 58, 33),      # Dark brown
    "S": (241, 196, 15),    # Sun/fire yellow
    "O": (230, 126, 34),    # Orange fire
    "C": (245, 246, 250),   # Cloud white
    "Y": (255, 255, 255),   # Pure white
    "V": (220, 221, 225),   # Light gray
    "I": (127, 143, 166),   # Medium gray
    "G": (165, 177, 194),   # Gray
    "A": (72, 84, 96),      # Dark gray
    "R": (255, 159, 243),   # Pink flower
    "P": (243, 104, 224),   # Pink center
    "F": (231, 76, 60),     # Fire red
}

# Sprite definitions (pixel art patterns)
TREE_SPRITE = [
    "TTTTTTTTTTKKKKKKTTTTTTTTTT",
    "TTTTTTTKKKMMMMMMKKKTTTTTTT",
    "TTTTTKKMMMMMMMMMMMMKKTTTTT",
    "TTTTKMMMMMMNNNNMMMMMMKTTTT",
    "TTTKMMMMMNNNNNNNNMMMMMKTTT",
    "TTKMMMMMNNNNNNNNNNMMMMMKTT",
    "TKMMMMMNNNNNNNNNNNNMMMMKTT",
    "TKMMMMNNNNNNNNNNNNNNMMMMKT",
    "KMMMMNNNNNNNNNNNNNNNNMMMMK",
    "KMMMNNNNNNNEEEENNNNNNNMMMK",
    "KMMMNNNNNNEEEEEEENNNNNMMMK",
    "KMMNNNNNNNEEEEEEEENNNNNMMK",
    "TKNNNNNNNNEEEEEEEENNNNNNKT",
    "TKNNNNNNNNEEEEEEEENNNNNNKT",
    "TTKNNNNNNNEEEEEEEENNNNNKTT",
    "TTTKKNNNNNEEEEEEENNNNKKTTT",
    "TTTTTKKNNNEEEEEENNNKKTTTTT",
    "TTTTTTTKKNEEEEEENKKTTTTTTT",
    "TTTTTTTTTKKEEEEKKTTTTTTTTT",
    "TTTTTTTTTTTKBBKTTTTTTTTTTT",
    "TTTTTTTTTTTKBDBKTTTTTTTTTT",
    "TTTTTTTTTTTKBDBKTTTTTTTTTT",
    "TTTTTTTTTTTKKKKKTTTTTTTTTT",
    "TTTTTTTTTTTKKKKKTTTTTTTTTT",
    "TTTTTTTTTTKKKKKKKTTTTTTTTT",
    "TTTTTTTTTKKKKKKKKKTTTTTTTT",
    "TTTTTTTTTKKKKKKKKKTTTTTTTT",
]

BONFIRE_1 = [
    "TTTTTFTTTTT", "TTTTFOFTTTT", "TTTOOOFTTTT",
    "TTFOOSOFTTT", "TFOOSSOOFTT", "TFOOSSSOFTT",
    "FOOSSSSSOFT", "KDKKBBKKDKT", "TKDBKKBDKTT", "TTKKKKKTTTT",
]

BONFIRE_2 = [
    "TTTTTTFTTTT", "TTTTTFOFTTT", "TTTTOOFTTTT",
    "TTTOOSOFTTT", "TTFOOSOOFTT", "TFOOSSSOFTT",
    "FOOSSSSSOFT", "KDKKBBKKDKT", "TKDBKKBDKTT", "TTKKKKKTTTT",
]

BUSH_SPRITE = [
    "TTTTTTMMMMMNTTTTTT",
    "TTTTMMMMMMNNNNTTTT",
    "TTTMMMMMMNNNNNETTT",
    "TTMMMMMMMNNNNNEETT",
    "TMMMMMMNNNNNEEEEET",
    "MMMMMNNNNNEEEEEEEE",
    "MMMMNNNNNNEEEEEEEE",
]

FLOWER_SPRITE = ["TRT", "RPR", "TRT", "TNT", "MNN"]
ROCK_SPRITE = ["TTGGTT", "TGGGGT", "GDDGGA", "DAAADA"]

CLOUD_SPRITE = [
    "TTTTTTTTYYYYTTTTTTTT",
    "TTTTTTYYYYYYYYTTTTTT",
    "TTTTYYYYYYYYYYYYTTTT",
    "TTYYYYYYYYYYYYYYYYTT",
    "YYYYYYYYYYYYYYYYYYYY",
    "YYYYYYYYYYYYYYYYYYYY",
    "TYYYYYYYYYYYYYYYYYYT",
]


def get_color(char, season):
    """Get the color for a character based on season"""
    if char == "T":
        return None  # Transparent
    if char in BASE_COLORS:
        return BASE_COLORS[char]
    
    # Seasonal colors
    sc = SEASON_COLORS[season]
    if char == "M":
        return sc["leaf_main"]
    elif char == "N":
        return sc["leaf_normal"]
    elif char == "E":
        return sc["leaf_edge"]
    
    return (0, 0, 0)


def get_time_theme(hour):
    """Get theme name based on time of day"""
    if 6 <= hour < 9:
        return "manha"
    elif 9 <= hour < 17:
        return "dia"
    elif 17 <= hour < 18:
        return "tarde"
    else:
        return "noite"


def get_season_from_month(month, hemisphere="south"):
    """
    Get season from month number (1-12) based on hemisphere.
    FIXED: Proper season calculation
    """
    # Northern hemisphere seasons
    if month in [12, 1, 2]:
        north_season = "winter"
    elif month in [3, 4, 5]:
        north_season = "spring"
    elif month in [6, 7, 8]:
        north_season = "summer"
    else:  # 9, 10, 11
        north_season = "autumn"
    
    # Southern hemisphere is opposite
    if hemisphere == "south":
        season_map = {
            "winter": "summer",
            "summer": "winter",
            "spring": "autumn",
            "autumn": "spring"
        }
        return season_map[north_season]
    
    return north_season
