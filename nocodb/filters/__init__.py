from .factory import basic_filter_class_factory
from .logical import And, Not, Or
from ..core import WhereFilter
from typing import List, Union


# Basic comparison filters
EqFilter = basic_filter_class_factory("eq")
EqualFilter = EqFilter
NotEqualFilter = basic_filter_class_factory("neq")
GreaterThanFilter = basic_filter_class_factory("gt")
GreaterOrEqualFilter = basic_filter_class_factory("gte")  # v3 API uses 'gte' not 'ge'
LessThanFilter = basic_filter_class_factory("lt")
LessOrEqualFilter = basic_filter_class_factory("lte")  # v3 API uses 'lte' not 'le'
LikeFilter = basic_filter_class_factory("like")
NotLikeFilter = basic_filter_class_factory("nlike")  # v3 API: does not contain


class IsFilter(WhereFilter):
    """
    Filter for null/empty checks in NocoDB v3 API.

    Valid values: null, notnull, true, false, empty, notempty

    Usage:
        IsFilter("Status", "null") -> (Status,is,null)
        IsFilter("Active", "true") -> (Active,is,true)
    """
    VALID_VALUES = {"null", "notnull", "true", "false", "empty", "notempty"}

    def __init__(self, column_name: str, value: str):
        if value not in self.VALID_VALUES:
            raise ValueError(
                f"Invalid IsFilter value '{value}'. "
                f"Valid values: {', '.join(sorted(self.VALID_VALUES))}"
            )
        self.__column_name = column_name
        self.__value = value

    def get_where(self) -> str:
        return f"({self.__column_name},is,{self.__value})"


class InFilter(WhereFilter):
    """
    Filter for matching against a list of values in NocoDB v3 API.

    Usage:
        InFilter("Tags", ["urgent", "important"]) -> (Tags,in,urgent,important)
        InFilter("Status", ["open", "pending"]) -> (Status,in,open,pending)
    """
    def __init__(self, column_name: str, values: List[Union[str, int, float]]):
        if not values:
            raise ValueError("InFilter requires at least one value")
        self.__column_name = column_name
        self.__values = values

    def get_where(self) -> str:
        values_str = ",".join(str(v) for v in self.__values)
        return f"({self.__column_name},in,{values_str})"


class BetweenFilter(WhereFilter):
    """
    Filter for range matching in NocoDB v3 API.

    Usage:
        BetweenFilter("Date", "2024-01-01", "2024-12-31") -> (Date,btw,2024-01-01,2024-12-31)
        BetweenFilter("Age", 18, 65) -> (Age,btw,18,65)
    """
    def __init__(self, column_name: str, start: Union[str, int, float], end: Union[str, int, float]):
        self.__column_name = column_name
        self.__start = start
        self.__end = end

    def get_where(self) -> str:
        return f"({self.__column_name},btw,{self.__start},{self.__end})"


__all__ = [
    "And",
    "Not",
    "Or",
    "EqFilter",
    "EqualFilter",
    "NotEqualFilter",
    "GreaterThanFilter",
    "GreaterOrEqualFilter",
    "LessThanFilter",
    "LessOrEqualFilter",
    "LikeFilter",
    "NotLikeFilter",
    "IsFilter",
    "InFilter",
    "BetweenFilter",
]
