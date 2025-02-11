"""

Some general settings for the  Annotation Tool. A couple of these can be changed
from the tool, some need to be edited here if needed.

You need to hand in a secondconfig filewith settings for the annotation task.

"""

import sys


## Settings purely for display reasons

TITLE = "Action Annotator"

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



## Read task-specific settings so they can overrule what is in this file

if len(sys.argv) > 2:
    user_settings = open(sys.argv[2]).read()
    exec(user_settings)
