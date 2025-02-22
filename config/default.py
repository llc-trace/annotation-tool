"""

Some general default settings for the  Annotation Tool. A couple of these can be
changed from the tool, some need to be edited here if needed.

You need to hand in a second config file with settings for the annotation task.

"""

import sys


## Settings purely for display reasons

TITLE = "Action Annotator"

DEFAULT_VIDEO_WIDTH = 50    # video width in percentage of total width
DEFAULT_IMAGE_WIDTH = 100   # image width in pixels

# Number of frames printed from the context. The only numbers that make sense
# here are from 3 to probably 6
CONTEXT_SIZE = 5

# This determines how many seconds to the left and right the fine-tuning slider
# includes.
FINE_TUNING_WINDOW = 0.5

# The format used for the timepoints of the slider, other useful formats are
# HH:mm:ss, mm:ss.SSS and HH:mm:ss.SSS, which add hours and/or milliseconds.
SLIDER_TIME_FORMAT = 'mm:ss:SSS'

# Needed when initializing the session state
def create_object_pool():
    return set()

# These should be overruled by the task specific settings (other wise there would
# be nothing to do). They define what kind of annotation inputs are required and
# what kind of default values there are (the default dicitonary is a place holder
# for functionality yet to be added).
PREDICATES = {}
PROPERTIES = []
DEFAULTS = {}

# Default task name, should be overwritten in task configuration files
DEFAULT_TASK = 'Main'

# Some tasks don't care about tiers (aka annotation layers), but they exist
# anyway so these settings make sure that all annotations are at least assigned
# to a default tier.
USE_TIERS = False
DEFAULT_TIER = 'Default'

## Loading the task-specific settings which overrule what is in this file
if len(sys.argv) > 2:
    user_settings = open(sys.argv[2]).read()
    exec(user_settings)
