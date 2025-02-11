
TITLE = "DPIP Gesture Annotator"


def create_object_pool():
    return set()


PARTICIPANTS = ['Director1', 'Director2', 'Director3', 'Builder']


# Here we had a need to add default values to the text, so instead of 'TEXT' we
# also allow a default value.

PREDICATES = {

    'icon-GA': [
        {'type': 'ARG0', 'label': '**ARG0**', 'items': [PARTICIPANTS]},
        {'type': 'ARG1', 'label': '**ARG1**', 'items': ['TEXT']},
        {'type': 'ARG2', 'label': '**ARG2**', 'items': ['(a / actor)']}],

    'deixis-GA': [
        {'type': 'ARG0', 'label': '**ARG0**', 'items': [PARTICIPANTS]},
        {'type': 'ARG1', 'label': '**ARG1**', 'items': ['TEXT']},
        {'type': 'ARG2', 'label': '**ARG2**', 'items': ['TEXT']}],

    'emblem-GA': [
        {'type': 'ARG0', 'label': '**ARG0**', 'items': [PARTICIPANTS]},
        {'type': 'ARG1', 'label': '**ARG1**', 'items': ['TEXT']},
        {'type': 'ARG2', 'label': '**ARG2**', 'items': ['TEXT']}],

}
