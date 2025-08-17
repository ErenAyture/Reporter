from enum import StrEnum, auto


class ItemStatus(StrEnum):
    QUEUED   = auto()
    RUNNING  = auto()
    OK       = auto()       # at least one success → group OK
    ERROR    = auto()       # item failed


class GroupStatus(StrEnum):
    QUEUED   = auto()
    RUNNING  = auto()
    DONE     = auto()       # ≥1 OK item
    ERROR    = auto()       # all finished but 0 success