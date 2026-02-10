from enum import Enum

class CategoryEnum(str, Enum):
    FOOD = "Food"
    TRAVEL = "Travel"
    ENTERTAINMENT = "Entertainment"
    SHOPPING = "Shopping"
    EDUCATION = "Education"
    HEALTH = "Health"
    TECHNOLOGY = "Technology"
    LIFESTYLE = "Lifestyle"
    BUSINESS = "Business"
    SPORTS = "Sports"
    NEWS = "News"
    OTHER = "Other"

class PriceRangeEnum(str, Enum):
    CHEAP = "$"
    MODERATE = "$$"
    EXPENSIVE = "$$$"
    LUXURY = "$$$$"
