"""

Settings for DPIP Action Annotation. 

Overwrites settings in config.py.

"""


TITLE = "DPIP Action Annotator"

TASK = 'DPIP-Actions'
MULTIPLE_TIERS = True


def create_object_pool():
    pool = []
    for size in ('Large', 'Small'):
        for color in ('Green', 'Red', 'Blue', 'Yellow'):
            for identifier in range(1, 7):
                pool.append(f'{size}{color}Block{identifier}')
    return set(pool)


## Definitions that determine the the predicate creation widgets and their options

ABSOLUTE_LOCATIONS = ['Base', 'FirstLayerAboveBase', 'SecondLayerAboveBase', 'TopLayer']

# Relations taken from the propositions document, first the name used here then the
# name used in the document. All negations are ignored, the tool can use an extra
# marker for that if needed.
POSITIONAL_RELATIONS = {
    'on': 'is on',
    'left-of': 'is left of',
    'right-of': 'is right of',
    'behind': 'id behind',
    'in-front-of': 'is in front of',
    'above': 'is above',
    'below': 'is below',
    'touches':  'is touching' }

# This includes an instruction for the code to load blocks. Blocks in play are not
# available at configuration time.
BLOCKS = ['**session_state:blocks**']

LOCATIONS = BLOCKS + ABSOLUTE_LOCATIONS
RELATIONS = list(POSITIONAL_RELATIONS.keys())

# These labels are used in the predicate creation widget
OBJECT_LABEL = '**Object** (select a block)'
SOURCE_LABEL = '**Source** (select a relation and location or specify manually)'
TARGET_LABEL = '**Target** (select a relation and location or specify manually)'
DESTINATION_LABEL = '**Destination** (select a relation and location or specify manually)'
LOCATION_LABEL = '**Location** (select a relation and location or specify manually)'

PREDICATES = {

    # This is where we store information on what widgets to display for each predicate
    # and where prebuilt lists of options are handed in.

    'TURN': [
        {'type': 'Object', 'label': OBJECT_LABEL, 'items': [BLOCKS]}],

    'PUT': [
        {'type': 'Object', 'label': OBJECT_LABEL, 'items': [BLOCKS]},
        {'type': 'Location', 'label': LOCATION_LABEL, 'items': [RELATIONS, LOCATIONS, 'TEXT']}],

    'REMOVE': [
        {'type': 'Object', 'label': OBJECT_LABEL, 'items': [BLOCKS]},
        {'type': 'Location', 'label': LOCATION_LABEL, 'items': [RELATIONS, LOCATIONS, 'TEXT']}],

    'MOVE': [
        {'type': 'Object', 'label': OBJECT_LABEL, 'items': [BLOCKS]},
        {'type': 'Source', 'label': SOURCE_LABEL, 'items': [RELATIONS, LOCATIONS, 'TEXT']},
        {'type': 'Destination', 'label': DESTINATION_LABEL, 'items': [RELATIONS, LOCATIONS, 'TEXT']}],
}

# TODO: not quite sure how to do this in a way that is intuitive
DEFAULTS = {
    ('properties', 'Participant'): 'Builder'
}


USE_TIERS = True
