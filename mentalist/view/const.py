"""
    All constant values are declared here.
"""

import datetime
import math

cur_year = datetime.date.today().year
cur_year = math.ceil((cur_year + 5) / 5.) * 5

NUMBER_LIST = [
    ['small', '0-100'],
    ['basic', '0-1000'],
    ['full', '0-10000'],
    ['years', '1950-{}'.format(cur_year)]
]

SUBSTITUTION_CHECKS = ['a -> @', 'b -> 8', 'c -> (', 'd -> 6', 'e -> 3', 'f -> #', 'g -> 9', 'h -> #', 'i -> !', 'i -> 1', 'k -> <', 'l -> i', 'l -> 1', 'o -> 0', 'q -> 9', 's -> 5', 's -> $', 's -> z', 't -> +', 'v -> >', 'v -> <', 'x -> %', 'y -> ?']

DATE_FORMATS = ['mmddyy', 'ddmmyy', 'mmddyyyy', 'ddmmyyyy', 'mmyyyy', 'mmyy', 'mmdd']

SPECIAL_CHARACTERS = '''!@#$%^&*()-=_+`~[]{}\|/:;'"'''

SPECIAL_TYPES = ['One at a time', 'All together']
