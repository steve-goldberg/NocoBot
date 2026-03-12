import pytest

from .. import filters

from ..core import WhereFilter


@pytest.mark.parametrize(
    "filter_class, expected_operator",
    [
        (filters.EqFilter, "eq"),
        (filters.EqualFilter, "eq"),
        (filters.NotEqualFilter, "neq"),
        (filters.GreaterOrEqualFilter, "gte"),  # v3 API uses 'gte' not 'ge'
        (filters.GreaterThanFilter, "gt"),
        (filters.LessThanFilter, "lt"),
        (filters.LessOrEqualFilter, "lte"),  # v3 API uses 'lte' not 'le'
        (filters.LikeFilter, "like"),
        (filters.NotLikeFilter, "nlike"),  # v3 API: does not contain
    ],
)
def test_basic_filters_are_correctly_created(
    filter_class: WhereFilter, expected_operator: str
):
    test_filter = filter_class("column", "value")
    assert test_filter.get_where() == f"(column,{expected_operator},value)"


def test_or_filter():
    nick_filter = filters.EqFilter("nickname", "elchicodepython")
    country_filter = filters.EqFilter("country", "es")
    nick_or_country_filter = filters.Or(nick_filter, country_filter)
    # v3 API: no outer parentheses on logical operators
    assert (
        nick_or_country_filter.get_where()
        == "(nickname,eq,elchicodepython)~or(country,eq,es)"
    )


def test_and_filter():
    nick_filter = filters.EqFilter("nickname", "elchicodepython")
    country_filter = filters.EqFilter("country", "es")
    nick_and_country_filter = filters.And(nick_filter, country_filter)
    # v3 API: no outer parentheses on logical operators
    assert (
        nick_and_country_filter.get_where()
        == "(nickname,eq,elchicodepython)~and(country,eq,es)"
    )


def test_combined_filter():
    nick_filter = filters.EqFilter("nickname", "elchicodepython")
    country_filter = filters.EqFilter("country", "es")
    girlfriend_code = filters.EqFilter("gfcode", "404")
    current_mood_code = filters.EqFilter("moodcode", "418")
    or_filter = filters.Or(nick_filter, country_filter)
    and_filter = filters.And(girlfriend_code, current_mood_code)
    or_combined_filter = filters.Or(or_filter, and_filter)
    and_combined_filter = filters.And(or_filter, and_filter)

    # v3 API: no outer parentheses, flat structure
    assert (
        or_combined_filter.get_where()
        == "(nickname,eq,elchicodepython)~or(country,eq,es)~or(gfcode,eq,404)~and(moodcode,eq,418)"
    )
    assert (
        and_combined_filter.get_where()
        == "(nickname,eq,elchicodepython)~or(country,eq,es)~and(gfcode,eq,404)~and(moodcode,eq,418)"
    )


def test_not_filter():
    me = filters.EqFilter("nickname", "elchicodepython")
    not_me = filters.Not(me)
    assert not_me.get_where() == "~not(nickname,eq,elchicodepython)"


# =========================================================================
# v3-specific filter tests
# =========================================================================


def test_is_filter_null():
    """Test IsFilter for null check."""
    is_null = filters.IsFilter("Status", "null")
    assert is_null.get_where() == "(Status,is,null)"


def test_is_filter_notnull():
    """Test IsFilter for not null check."""
    is_not_null = filters.IsFilter("Status", "notnull")
    assert is_not_null.get_where() == "(Status,is,notnull)"


def test_is_filter_empty():
    """Test IsFilter for empty check."""
    is_empty = filters.IsFilter("Description", "empty")
    assert is_empty.get_where() == "(Description,is,empty)"


def test_is_filter_boolean():
    """Test IsFilter for boolean checks."""
    is_true = filters.IsFilter("Active", "true")
    is_false = filters.IsFilter("Archived", "false")
    assert is_true.get_where() == "(Active,is,true)"
    assert is_false.get_where() == "(Archived,is,false)"


def test_is_filter_invalid_value():
    """Test IsFilter raises error for invalid values."""
    with pytest.raises(ValueError) as exc_info:
        filters.IsFilter("Status", "invalid")
    assert "Invalid IsFilter value" in str(exc_info.value)


def test_in_filter():
    """Test InFilter for matching against list of values."""
    in_filter = filters.InFilter("Tags", ["urgent", "important"])
    assert in_filter.get_where() == "(Tags,in,urgent,important)"


def test_in_filter_single_value():
    """Test InFilter with single value."""
    in_filter = filters.InFilter("Status", ["open"])
    assert in_filter.get_where() == "(Status,in,open)"


def test_in_filter_numeric_values():
    """Test InFilter with numeric values."""
    in_filter = filters.InFilter("Priority", [1, 2, 3])
    assert in_filter.get_where() == "(Priority,in,1,2,3)"


def test_in_filter_empty_raises_error():
    """Test InFilter raises error for empty values."""
    with pytest.raises(ValueError) as exc_info:
        filters.InFilter("Tags", [])
    assert "at least one value" in str(exc_info.value)


def test_between_filter():
    """Test BetweenFilter for range matching."""
    between_filter = filters.BetweenFilter("Date", "2024-01-01", "2024-12-31")
    assert between_filter.get_where() == "(Date,btw,2024-01-01,2024-12-31)"


def test_between_filter_numeric():
    """Test BetweenFilter with numeric values."""
    between_filter = filters.BetweenFilter("Age", 18, 65)
    assert between_filter.get_where() == "(Age,btw,18,65)"


def test_not_like_filter():
    """Test NotLikeFilter for 'does not contain' matching."""
    not_like_filter = filters.NotLikeFilter("Name", "test")
    assert not_like_filter.get_where() == "(Name,nlike,test)"


# =========================================================================
# v3 filter combinations - complex scenarios
# =========================================================================


def test_v3_filter_with_logical_and():
    """Test combining v3 filters (gte, lte) with And operator."""
    min_filter = filters.GreaterOrEqualFilter("price", "10")
    max_filter = filters.LessOrEqualFilter("price", "100")
    price_range = filters.And(min_filter, max_filter)
    # v3 API: gte/lte operators with ~and logical
    assert price_range.get_where() == "(price,gte,10)~and(price,lte,100)"


def test_v3_is_filter_with_or():
    """Test combining IsFilter with Or operator."""
    null_filter = filters.IsFilter("Status", "null")
    empty_filter = filters.IsFilter("Status", "empty")
    null_or_empty = filters.Or(null_filter, empty_filter)
    assert null_or_empty.get_where() == "(Status,is,null)~or(Status,is,empty)"


def test_v3_in_filter_with_not():
    """Test combining InFilter with Not operator."""
    in_filter = filters.InFilter("Category", ["spam", "trash"])
    not_in = filters.Not(in_filter)
    assert not_in.get_where() == "~not(Category,in,spam,trash)"


def test_v3_between_filter_with_and():
    """Test combining BetweenFilter with And for compound range queries."""
    date_range = filters.BetweenFilter("created_at", "2024-01-01", "2024-12-31")
    status_filter = filters.EqFilter("status", "active")
    combined = filters.And(date_range, status_filter)
    assert combined.get_where() == "(created_at,btw,2024-01-01,2024-12-31)~and(status,eq,active)"


def test_v3_nested_logical_operators():
    """Test deeply nested logical operators with v3 format."""
    # Build: (A OR B) AND (C OR D)
    a = filters.EqFilter("field_a", "1")
    b = filters.EqFilter("field_b", "2")
    c = filters.EqFilter("field_c", "3")
    d = filters.EqFilter("field_d", "4")

    ab_or = filters.Or(a, b)
    cd_or = filters.Or(c, d)
    combined = filters.And(ab_or, cd_or)

    # v3 API flattens nested logical operators
    assert combined.get_where() == "(field_a,eq,1)~or(field_b,eq,2)~and(field_c,eq,3)~or(field_d,eq,4)"
