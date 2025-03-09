"""

Some general default settings for the  Annotation Tool. A couple of these can be
changed from the tool, some need to be edited here if needed.

You need to hand in a second config file with settings for the annotation task.

"""

import sys


TITLE = "Action Annotator"

# Video settings
DEFAULT_VIDEO_WIDTH = 50    # video width in percentage of total width
DEFAULT_IMAGE_WIDTH = 100   # image width in pixels

# Number of frames printed from the context window. The only numbers that make
# sense here are from 3 to probably 6.
CONTEXT_SIZE = 5

# Spacing between frames in the context window, in milliseconds.
CONTEXT_STEP = 100

# This determines how many seconds to the left and right the fine-tuning slider
# includes.
FINE_TUNING_WINDOW = 0.5

# The format used for the timepoints of the slider, other useful formats are
# HH:mm:ss, mm:ss.SSS and HH:mm:ss.SSS, which add hours and/or milliseconds.
SLIDER_TIME_FORMAT = 'mm:ss:SSS'

# Empty object pool by default
OBJECT_POOL = {}

# These should be overruled by the task specific settings (other wise there would
# be nothing to do). They define what kind of annotation inputs are required and
# what kind of default values there are (the default dicitonary is a place holder
# for functionality yet to be added).
PREDICATES = {}
PROPERTIES = []
DEFAULTS = {}

# Default task name, should be overwritten in task configuration files
TASK = 'Main'

# Some tasks don't care about tiers (aka annotation layers), but they exist
# anyway so these settings make sure that all annotations are at least assigned
# to a default tier, it is strongly suggested that you overwrite this in a task
# specific configuration.
TIER = 'Default'

# By default, use only one tier and don't let the tier be defined by the
# annotator but by the configuration file.
MULTIPLE_TIERS = False
TIER_IS_DEFINED_BY_USER = False

# Loading the task-specific settings which overrule what is in this file
if len(sys.argv) > 2:
    user_settings = open(sys.argv[2]).read()
    exec(user_settings)
