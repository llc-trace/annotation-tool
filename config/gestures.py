"""

Settings for General Gesture Annotation. 

Overwrites settings in config.py.

"""

TITLE = "Gesture Annotator"


PREDICATES = {

    'icon-GA': [
        {'type': 'ARG0', 'label': '**ARG0**', 'items': ['TEXT']},
        {'type': 'ARG1', 'label': '**ARG1**', 'items': ['TEXT']},
        {'type': 'ARG2', 'label': '**ARG2**', 'items': ['TEXT']}],

    'deixis-GA': [
        {'type': 'ARG0', 'label': '**ARG0**', 'items': ['TEXT']},
        {'type': 'ARG1', 'label': '**ARG1**', 'items': ['TEXT']},
        {'type': 'ARG2', 'label': '**ARG2**', 'items': ['TEXT']}],

    'emblem-GA': [
        {'type': 'ARG0', 'label': '**ARG0**', 'items': ['TEXT']},
        {'type': 'ARG1', 'label': '**ARG1**', 'items': ['TEXT']},
        {'type': 'ARG2', 'label': '**ARG2**', 'items': ['TEXT']}],
}

PROPERTIES = [

    {'type': 'comment', 'label': '**Comment (optional)**', 'items': ['TEXT'], 'optional': True}
]

DEFAULT_TIER = 'Gestures'
