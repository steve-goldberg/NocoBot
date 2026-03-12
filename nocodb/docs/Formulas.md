# NocoDB Formula Reference

Complete reference for all formula functions and operators available in NocoDB formula fields.

---

## Numeric and Logical Operators

### Numeric operators

| Operator | Sample | Description |
| --- | --- | --- |
| `+` | `{field1} + {field2} + 2` | Addition of numeric values |
| `-` | `{field1} - {field2}` | Subtraction of numeric values |
| `*` | `{field1} * {field2}` | Multiplication of numeric values |
| `/` | `{field1} / {field2}` | Division of numeric values |

### Logical operators

| Operator | Sample | Description |
| --- | --- | --- |
| `<` | `{field1} < {field2}` | Less than |
| `>` | `{field1} > {field2}` | Greater than |
| `<=` | `{field1} <= {field2}` | Less than or equal to |
| `>=` | `{field1} >= {field2}` | Greater than or equal to |
| `==` | `{field1} == {field2}` | Equal to |
| `!=` | `{field1} != {field2}` | Not equal to |

### String operators

| Operator | Sample | Description |
| --- | --- | --- |
| `&` | `{field1} & {field2}` | String concatenation |

---

## Numeric Functions

### ABS

Returns the distance of the number from zero on the number line (absolute value).

```
ABS(number)
```

```
ABS(10.35) => 10.35
ABS(-15) => 15
```

### ADD

Computes the total of multiple numbers.

```
ADD(number1, [number2, ...])
```

```
ADD(5, 7) => 12
ADD(-10, 15, 20) => 25
```

### AVG

Calculates the mean of a set of numerical values.

```
AVG(number1, [number2, ...])
```

```
AVG(10, 20, 30) => 20
AVG(-5, 5) => 0
```

### CEILING

Rounds a number up to the nearest integer greater than or equal to the input.

```
CEILING(number)
```

```
CEILING(8.75) => 9
CEILING(-15.25) => -15
```

### COUNT

Calculates the number of numeric arguments provided.

```
COUNT(number1, [number2, ...])
```

```
COUNT(1, 2, "abc", 3) => 3
COUNT(-5, 0, "$abc", 5) => 3
```

### COUNTA

Counts the number of non-empty arguments provided.

```
COUNTA(value1, [value2, ...])
```

```
COUNTA(1, "", "text") => 2
COUNTA("one", "two", "three") => 3
```

### COUNTALL

Calculates the total number of arguments, both numeric and non-numeric.

```
COUNTALL(value1, [value2, ...])
```

```
COUNTALL(1, "", "text") => 3
COUNTALL("one", "two", "three") => 3
```

### EVEN

Rounds positive values up to the nearest even number and negative values down to the nearest even number.

```
EVEN(number)
```

```
EVEN(7) => 8
EVEN(-5) => -6
```

### EXP

Returns 'e' raised to the power of a given number.

```
EXP(number)
```

```
EXP(2) => 7.38905609893065
EXP(-1) => 0.36787944117144233
```

### FLOOR

Rounds a number down to the nearest integer.

```
FLOOR(number)
```

```
FLOOR(8.75) => 8
FLOOR(-15.25) => -16
```

### INT

Truncates the decimal part, returning the integer portion of a number.

```
INT(number)
```

```
INT(8.75) => 8
INT(-15.25) => -15
```

### LOG

Computes the logarithm of a number to a specified base (default = e).

```
LOG([base], number)
```

```
LOG(10, 100) => 2
LOG(2, 8) => 3
```

### MAX

Returns the highest value from a set of numbers.

```
MAX(number1, [number2, ...])
```

```
MAX(5, 10, 3) => 10
MAX(-10, -5, -20) => -5
```

### MIN

Returns the lowest value from a set of numbers.

```
MIN(number1, [number2, ...])
```

```
MIN(5, 10, 3) => 3
MIN(-10, -5, -20) => -20
```

### MOD

Calculates the remainder when dividing one number by another.

```
MOD(number1, number2)
```

```
MOD(10, 3) => 1
MOD(-15, 4) => -3
```

### ODD

Rounds positive values up to the nearest odd number and negative values down to the nearest odd number.

```
ODD(number)
```

```
ODD(6) => 7
ODD(-5.5) => -7
```

### POWER

Raises a given base to a specified exponent.

```
POWER(base, exponent)
```

```
POWER(2, 3) => 8
POWER(10, -2) => 0.01
```

### ROUND

Rounds a number to a specified number of decimal places (default precision = 0).

```
ROUND(number, [precision])
```

```
ROUND(8.765, 2) => 8.77
ROUND(-15.123, 1) => -15.1
```

### ROUNDDOWN

Rounds a number down to a specified number of decimal places (default precision = 0).

```
ROUNDDOWN(number, [precision])
```

```
ROUNDDOWN(8.765, 2) => 8.76
ROUNDDOWN(-15.123, 1) => -15.2
```

### ROUNDUP

Rounds a number up to a specified number of decimal places (default precision = 0).

```
ROUNDUP(number, [precision])
```

```
ROUNDUP(8.765, 2) => 8.77
ROUNDUP(-15.123, 1) => -15.1
```

### SQRT

Calculates the square root of a given number.

```
SQRT(number)
```

```
SQRT(25) => 5
SQRT(2) => 1.4142135623730951
```

### VALUE

Extracts the numeric value from a string (handles `%` or `-` accordingly).

```
VALUE(text)
```

```
VALUE("123$") => 123
VALUE("USD -45.67") => -45.67
```

---

## String Functions

### CONCAT

Concatenates one or more strings into a single string.

```
CONCAT(text, [text,...])
```

```
CONCAT('John', ' ', 'Doe') => 'John Doe'
```

### LEFT

Retrieves the first 'n' characters from the beginning of the input string.

```
LEFT(text, count)
```

```
LEFT('123-456-7890', 3) => '123'
```

### LEN

Returns the total number of characters in the provided string.

```
LEN(text)
```

```
LEN('Product Description') => 19
```

### LOWER

Transforms all characters in the input string to lowercase.

```
LOWER(text)
```

```
LOWER('User INPUT') => 'user input'
```

### MID

Retrieves a substring starting at the specified position for the specified count of characters.

```
MID(text, position, [count])
```

```
MID('This is a sentence', 5, 3) => 'is '
```

### REGEX_EXTRACT

Searches the input string for the first occurrence of the specified regex pattern and returns the matched substring.

```
REGEX_EXTRACT(text, pattern)
```

```
REGEX_EXTRACT('Error: Something went wrong', 'Error: (.*)') => 'Something went wrong'
```

### REGEX_MATCH

Returns 1 if the input string matches the specified regex pattern, 0 otherwise.

```
REGEX_MATCH(text, pattern)
```

```
REGEX_MATCH('123-45-6789', '\d{3}-\d{2}-\d{4}') => 1
```

### REGEX_REPLACE

Replaces all occurrences of the specified regex pattern with the provided replacement string.

```
REGEX_REPLACE(text, pattern, replacer)
```

```
REGEX_REPLACE('Replace all bugs', 'bug', 'feature') => 'Replace all features'
```

### REPEAT

Duplicates the provided string the specified number of times.

```
REPEAT(text, count)
```

```
REPEAT('ab', 3) => 'ababab'
```

### REPLACE

Replaces all instances of a substring with another substring.

```
REPLACE(text, srchStr, rplcStr)
```

```
REPLACE('Replace old text', 'old', 'new') => 'Replace new text'
```

### RIGHT

Retrieves the last 'n' characters from the end of the input string.

```
RIGHT(text, n)
```

```
RIGHT('file_name.txt', 3) => 'txt'
```

### SEARCH

Returns the position of the specified substring within the input string (0 if not found).

```
SEARCH(text, srchStr)
```

```
SEARCH('user@example.com', '@') => 5
```

### SUBSTR

Extracts a substring starting at the specified position, optionally for a specified count of characters.

```
SUBSTR(text, position, [count])
```

```
SUBSTR('Extract this text', 9, 4) => 'this'
```

### TRIM

Eliminates any leading or trailing whitespaces from the input string.

```
TRIM(text)
```

```
TRIM('   Trim this   ') => 'Trim this'
```

### UPPER

Transforms all characters in the input string to uppercase.

```
UPPER(text)
```

```
UPPER('title') => 'TITLE'
```

### URL

Checks if the input string is a valid URL and converts it into a hyperlink.

```
URL(text)
```

```
URL('https://www.example.com') => a clickable link for https://www.example.com
```

### URLENCODE

Percent-encodes special characters in a string so it can be used as a URL query parameter. Similar to JavaScript `encodeURIComponent()` but only encodes characters with special meaning per RFC 3986 section 2.2, plus percent signs and spaces.

```
URLENCODE(text)
```

```
'https://example.com/q?param=' & URLENCODE('Hello, world')
=> 'https://example.com/q?param=Hello%2C%20world'
```

### ISBLANK

Returns TRUE if the input is empty or null, FALSE otherwise.

```
ISBLANK(text)
```

```
ISBLANK('') => true
ISBLANK('Hello') => false
```

### ISNOTBLANK

Returns TRUE if the input has a value, FALSE if empty or null.

```
ISNOTBLANK(text)
```

```
ISNOTBLANK('') => false
ISNOTBLANK('Hello') => true
```

---

## Date Functions

### DATETIME_DIFF

Calculates the difference between two dates in various units. Positive values indicate date2 is in the past relative to date1; negative values indicate the opposite.

```
DATETIME_DIFF(date1, date2, ["milliseconds" | "ms" | "seconds" | "s" | "minutes" | "m" | "hours" | "h" | "days" | "d" | "weeks" | "w" | "months" | "M" | "quarters" | "Q" | "years" | "y"])
```

```
DATETIME_DIFF("2022/10/14", "2022/10/15", "seconds") => -86400
```

### DATEADD

Adds a specified value to a date or datetime. Supports negative values and units down to seconds.

```
DATEADD(date | datetime, value, ["second" | "minute" | "hour" | "day" | "week" | "month" | "year"])
```

```
DATEADD('2022-03-14 10:00:00', 30, 'second')  => 2022-03-14 10:00:30
DATEADD('2022-03-14 10:00:00', 15, 'minute')  => 2022-03-14 10:15:00
DATEADD('2022-03-14 10:00:00', 2, 'hour')     => 2022-03-14 12:00:00
DATEADD('2022-03-14', 1, 'day')               => 2022-03-15
DATEADD('2022-03-14', 1, 'week')              => 2022-03-21
DATEADD('2022-03-14', 1, 'month')             => 2022-04-14
DATEADD('2022-03-14', 1, 'year')              => 2023-03-14
```

Conditional example:

```
IF(NOW() < DATEADD(date, 10, 'day'), "true", "false")
```

### NOW

Returns the current date and time.

```
NOW()
```

```
NOW() => 2022-05-19 17:20:43
```

### WEEKDAY

Returns the day of the week as an integer (0-6). Monday is the default start day; optionally specify a different start day.

```
WEEKDAY(date, [startDayOfWeek])
```

```
WEEKDAY(NOW()) => 0 (if today is Monday)
WEEKDAY(NOW(), "sunday") => 1 (if today is Monday)
```

### DATESTR

Converts a date or datetime field into a string in "YYYY-MM-DD" format, ignoring the time part.

```
DATESTR(date | datetime)
```

```
DATESTR('2022-03-14') => 2022-03-14
DATESTR('2022-03-14 12:00:00') => 2022-03-14
```

### DAY

Returns the day of the month as an integer (1-31). Based on server timezone (GMT by default).

```
DAY(date | datetime)
```

```
DAY('2022-03-14') => 14
```

### MONTH

Returns the month of the year as an integer (1-12). Based on server timezone (GMT by default).

```
MONTH(date | datetime)
```

```
MONTH('2022-03-14') => 3
```

### YEAR

Returns the year as an integer. Based on server timezone (GMT by default).

```
YEAR(date | datetime)
```

```
YEAR('2022-03-14') => 2022
```

### HOUR

Returns the hour of the day as an integer (0-23, 24-hour clock). Based on server timezone (GMT by default).

```
HOUR(datetime)
```

```
HOUR('2022-03-14 12:00:00') => 12
```

---

## Array Functions

### ARRAYSORT

Sorts an array result from links or lookup fields.

```
ARRAYSORT(array, ["asc" | "desc"])
```

```
ARRAYSORT({LookupField}, "desc")
```

The second parameter determines sort order, defaulting to "asc" if omitted.

### ARRAYUNIQUE

Returns unique items from the given array, eliminating duplicates.

```
ARRAYUNIQUE(array)
```

```
ARRAYUNIQUE({Field})
```

### ARRAYCOMPACT

Removes null and empty values from an array, retaining only populated items.

```
ARRAYCOMPACT(array)
```

```
ARRAYCOMPACT({Field})
```

### ARRAYSLICE

Extracts a subset of an array from start index to optional end index. Indices start at 1. Both must be positive, with end >= start; invalid ranges return empty results.

```
ARRAYSLICE(array, start, [end])
```

```
ARRAYSLICE({Field}, 2, 3)
```

---

## Conditional Expressions

### IF

Evaluates a condition and returns one value if TRUE, another if FALSE.

```
IF(expr, successCase, elseCase)
```

```
IF({field} > 1, Value1, Value2)
```

- Returns `Value1` if `{field} > 1` evaluates to TRUE
- Returns `Value2` otherwise

### SWITCH

Evaluates an expression against a series of patterns and returns the corresponding value of the first match. Returns the default value if no patterns match.

```
SWITCH(expr, [pattern, value, ..., default])
```

```
SWITCH({field}, 1, 'One', 2, 'Two', '--')
```

- `'One'` if `{field} = 1`
- `'Two'` if `{field} = 2`
- `'--'` for the default case

### AND

Returns TRUE only if all its conditions are true.

```
AND(expr1, [expr2,...])
```

```
AND({field} > 2, {field} < 10)
```

### OR

Returns TRUE if at least one of its conditions is true.

```
OR(expr1, [expr2,...])
```

```
OR({field} > 2, {field} < 10)
```

### Conditional examples

```
IF({marksSecured} > 80, "GradeA", "GradeB")
```

```
SWITCH({quarterNumber},
    1, 'Jan-Mar',
    2, 'Apr-Jun',
    3, 'Jul-Sep',
    4, 'Oct-Dec',
    'INVALID'
)
```

---

## JSON Functions

### JSON_EXTRACT

Extracts a value from a JSON string using jq-like dot notation.

```
JSON_EXTRACT(json_string, path)
```

```
JSON_EXTRACT('{"a": {"b": "c"}}', '.a.b') => "c"
JSON_EXTRACT({json_column}, '.key')
```

- `json_string` must be a valid JSON string
- `path` follows jq-like dot notation (e.g., `.a.b` to access nested values)
- Returns the extracted value as a string

---

## Generic Functions

### RECORD_ID

Returns the unique identifier of the record.

```
RECORD_ID()
```

```
RECORD_ID() => 1
```

---

## Formatting Formula Results

Formatting the output of formulas allows you to tailor how your data is displayed based on the type of result.

### Numeric Formats

#### Decimal

Displays results with a specified number of decimal places, allowing you to define the precision.

#### Currency

Displays monetary values with the option to set and display a specific currency symbol.

#### Percent

Displays results as a number with an option to configure it as a progress bar.

#### Rating

Ideal for ratings on a scale from 1 to 10. Allows customization of icon, color, and maximum rating value.

### Date Formats

#### Date Time

Displays both date and time values.

#### Date

Displays only date values, with a wide range of date formats available.

#### Time

Displays the result in either 12-hour or 24-hour time format.

### Text Formats

#### Email

Displays results as clickable mailto links.

#### URL

Displays results as clickable web links/hyperlinks.

#### Phone Number

Displays results as phone numbers.

### Boolean Format

#### Checkbox

When NocoDB recognizes a formula's output as a Boolean result, the Checkbox format displays it similar to a checkbox field. Icon and color are customizable.

---

## Date/Time Format Reference

### Supported date formats

| Format | Example |
| --- | --- |
| YYYY-MM-DD | 2023-09-22 |
| YYYY/MM/DD | 2023/09/22 |
| DD-MM-YYYY | 22-09-2023 |
| MM-DD-YYYY | 09-22-2023 |
| DD/MM/YYYY | 22/09/2023 |
| MM/DD/YYYY | 09/22/2023 |
| DD MM YYYY | 22 09 2023 |
| MM DD YYYY | 09 22 2023 |
| YYYY MM DD | 2023 09 22 |
| DD MMM YYYY | 22 JAN 2024 |
| DD MMM YY | 22 JAN 24 |
| DD.MM.YYYY | 15.09.2024 |
| DD.MM.YY | 15.09.24 |

### Supported time formats

| Format | Example |
| --- | --- |
| HH:mm:ss | 12:45:30 |
| HH:mm | 14:20 |
