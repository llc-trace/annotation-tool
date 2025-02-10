"""

Settings for the DPIP Annotation Tool. A couple of these can be changed from the
tool, but most need to be edited here if needed. Alternatively, you can hand in a
second configuration file that overwrites settings in here.

"""

import sys


## Settings purely for display reasons

DEFAULT_VIDEO_WIDTH = 50    # video width in percentage of total width
DEFAULT_IMAGE_WIDTH = 100   # image width in pixels

# Number of frames printed from the context. Theonly numbers that make sense
# here are from 3 to probably 6
CONTEXT_SIZE = 5

# This determines how many seconds to the left and right the fine-tuning slider
# includes.
FINE_TUNING_WINDOW = 0.5

# The format used for the timepoints of the slider, other useful formats are
# 'HH:mm:ss' (if you have a longer video), 'mm:ss.SSS' (if you want to show
# milliseconds), or 'HH:mm:ss.SSS' (if you want both).
SLIDER_TIME_FORMAT = 'mm:ss:SSS'


## Settings that refer to the content of the annotation

def create_object_pool():
    pool = []
    for size in ('Large', 'Small'):
        for color in ('Green', 'Red', 'Blue', 'Yellow'):
            for identifier in range(1, 7):
                pool.append(f'{size}{color}Block{identifier}')
    return set(pool)

PARTICIPANTS = ('Director1', 'Director2', 'Director3', 'Builder')

ACTION_TYPES = {
    'PUT': ['Object', 'Location'],
    'REMOVE': ['Object', 'Location'],
    'MOVE': ['Object', 'Source', 'Destination'],
    'TURN': ['Object'] }

GESTURE_TYPES = {
    'POINT': ['Direction'],
    'PUSH-LEFT': [],
    'PUSH-RIGHT': []}

ABSOLUTE_LOCATIONS = ['Base', 'FirstLayerAboveBase', 'SecondLayerAboveBase', 'TopLayer']

LOCATION_TYPES = ['Location', 'Source', 'Destination']

# Mapping the argument types to strings that are displayed in the argument creation widget
ARGUMENT_MAPPINGS = {
    'Object': '**Object** (select a block)',
    'Source': '**Source** (select a relation and location or specify manually)',
    'Target': '**Target** (select a relation and location or specify manually)',
    'Destination': '**Destination** (select a relation and location or specify manually)',
    'Location': '**Location** (select a relation and location or specify manually)'}


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
    'touches':  'is touching'
}


TYPES = {}

OBJECTS = list(sorted(create_object_pool()))
LOCATIONS = OBJECTS + ABSOLUTE_LOCATIONS
RELATIONS = list(POSITIONAL_RELATIONS.keys())



PREDICATES = {

    'TURN': [
        {'type': 'Object', 'label': '**Object**', 'items': [OBJECTS]}],

    'PUT': [
        {'type': 'Object', 'label': '**Object**', 'items': [OBJECTS]},
        {'type': 'Location', 'label': '**Location**', 'items': [RELATIONS, LOCATIONS, 'TEXT']}],

    'REMOVE': [
        {'type': 'Object', 'label': '**Object**', 'items': [OBJECTS]},
        {'type': 'Location', 'label': '**Location**', 'items': [RELATIONS, LOCATIONS, 'TEXT']}],

    'MOVE': [
        {'type': 'Object', 'label': '**Object**', 'items': [OBJECTS]},
        {'type': 'Source', 'label': '**Source**', 'items': [RELATIONS, LOCATIONS, 'TEXT']},
        {'type': 'Destination', 'label': '**Destination**', 'items': [RELATIONS, LOCATIONS, 'TEXT']}],
}


# Read user settings so they can overrule what is in this file

if len(sys.argv) > 2:
    user_settings = open(sys.argv[2]).read()
    exec(user_settings)
