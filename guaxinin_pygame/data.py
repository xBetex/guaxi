# data.py
SEASON_SKIES = {
    "summer": [
        (25, 70, 170),
        (100, 185, 230),
        (180, 220, 240)
    ],
    "autumn": [
        (20, 55, 140),
        (120, 150, 170),
        (190, 185, 175)
    ],
    "winter": [
        (15, 40, 110),
        (90, 130, 165),
        (170, 185, 190)
    ],
    "spring": [
        (30, 75, 165),
        (120, 190, 220),
        (195, 220, 230)
    ]
}

CRATERS = [
    (0.10, -0.20, 0.30),
    (-0.26, 0.14, 0.24),
    (0.38, -0.08, 0.18),
    (0.20, -0.32, 0.15),
    (-0.37, 0.26, 0.11),
    (0.52, 0.34, 0.10),
    (-0.16, -0.54, 0.08),
    (0.20, 0.57, 0.07),
    (-0.52, -0.12, 0.09),
    (0.42, -0.42, 0.07),
    (-0.42, 0.44, 0.06),
    (0.08, 0.12, 0.16),
]

def get_season(day, southern=True):
    if southern:
        if day <= 79:
            return "summer"
        elif day <= 171:
            return "autumn"
        elif day <= 263:
            return "winter"
        elif day <= 354:
            return "spring"
        return "summer"
    else:
        if day <= 79:
            return "winter"
        elif day <= 171:
            return "spring"
        elif day <= 263:
            return "summer"
        elif day <= 354:
            return "autumn"
        return "winter"

def get_month_name(day):
    months = [
        ("Jan", 31),
        ("Feb", 28),
        ("Mar", 31),
        ("Apr", 30),
        ("May", 31),
        ("Jun", 30),
        ("Jul", 31),
        ("Aug", 31),
        ("Sep", 30),
        ("Oct", 31),
        ("Nov", 30),
        ("Dec", 31),
    ]

    d = day
    for name, count in months:
        if d < count:
            return name
        d -= count

    return "Dec"