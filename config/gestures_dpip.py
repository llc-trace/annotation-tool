"""

Settings for DPIP Gesture Annotation. 

Overwrites settings in config.py.

"""

TITLE = "DPIP Gesture Annotator"

TASK = "DPIP-Gestures"
TIER = None

MULTIPLE_TIERS = True
TIER_IS_DEFINED_BY_USER = True

PARTICIPANTS = ['Director1', 'Director2', 'Director3', 'Builder']
TIERS = [f'GESTURES-{participant}' for participant in PARTICIPANTS]


PREDICATES = {

    'icon-GA': [
        {'type': 'ARG0', 'label': '**ARG0**', 'items': [PARTICIPANTS]},
        {'type': 'ARG1', 'label': '**ARG1**', 'items': ['TEXT']},
        {'type': 'ARG2', 'label': '**ARG2**', 'items': ['TEXT']}],

    'deixis-GA': [
        {'type': 'ARG0', 'label': '**ARG0**', 'items': [PARTICIPANTS]},
        {'type': 'ARG1', 'label': '**ARG1**', 'items': ['TEXT']},
        {'type': 'ARG2', 'label': '**ARG2**', 'items': ['TEXT']}],

    'emblem-GA': [
        {'type': 'ARG0', 'label': '**ARG0**', 'items': [PARTICIPANTS]},
        {'type': 'ARG1', 'label': '**ARG1**', 'items': ['TEXT']},
        {'type': 'ARG2', 'label': '**ARG2**', 'items': ['TEXT']}],
}


PROPERTIES = [

    {'type': 'comment', 'label': '**Comment (optional)**', 'items': ['TEXT'], 'optional': True}
]
