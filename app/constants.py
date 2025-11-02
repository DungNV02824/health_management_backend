from enum import Enum


class UserProviders(str, Enum):
    PORTAL = "portal"
    GOOGLE = "google"
