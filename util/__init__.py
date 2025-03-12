"""

Basic Utilities for the annotator

"""


import sys
import datetime

import streamlit as st

from config import default as config
from util.video import TimePoint, TimeFrame


def get_timeline(annotations: list) -> list:
    basetime = '1999-01-01T00'
    items = []
    for n, annotation in enumerate(annotations):
        items.append({
            "id": annotation.identifier, "content": annotation.name,
            "group": annotation.tier,
            "start": f'{basetime}:{annotation.start_as_string()}',
            "annotation": annotation.as_json()})
    return items

def get_window(milliseconds: int, n=config.CONTEXT_SIZE, step=config.CONTEXT_STEP) -> list:
    """Returns a list of timepoints (in milliseconds) in a window around the given
    timepoint in milliseconds."""
    timepoints = []
    for ms in range(n * -step, 0, step):
        timepoints.append(milliseconds + ms)
    timepoints.append(milliseconds)
    for ms in range(0, n * step, step):
        timepoints.append(milliseconds + ms + step)
    return timepoints

def get_command_line_options() -> dict:
    video_path = sys.argv[1]
    config_path = sys.argv[2]
    debug = True if (len(sys.argv) > 3 and sys.argv[3] == 'debug') else False
    return {'video_path': video_path, 'config_path': config_path, 'debug': debug}

def create_timeframe_from_slider_inputs(t1, t2):
    # after initial selection we do not have milliseconds yet
    return TimeFrame(TimePoint(hours=t1.hour, minutes=t1.minute, seconds=t1.second),
                     TimePoint(hours=t2.hour, minutes=t2.minute, seconds=t2.second),
                     video=st.session_state.video)

def timestamp():
    return datetime.datetime.now().strftime('%Y%m%d:%H%M%S')

def log(text: str):
    with open(st.session_state.io['log'], 'a') as fh:
        fh.write(f'INFO  {timestamp()}\t{text}\n')

def debug(header: str, body: str = ''):
    if st.session_state.debug:
        ts = timestamp()
        with open(st.session_state.io['log'], 'a') as fh:
            fh.write(f'DEBUG {ts}\t{header}\n')
            print(f'DEBUG {ts}\t{header}')
            if body:
                print(body)
                for line in body.split('\n'):
                    fh.write(f'DEBUG {line}\n')

def create_label(text: str, size='normalsize'):
    """Return formatted text that can be used as a label of a particular size,
    for sizes use the ones defined by LaTeX (small, large, Large, etcetera)."""
    return r"$\textsf{" + f'\\{size} {text}' + "}$"

def current_timeframes(task: str) -> list:
    """Returns all <name, timeframe> pairs of the current annotations in the task."""
    annos = st.session_state.annotations
    return [(anno.name, anno.timeframe) for anno in annos if anno.task == task]

def process_arguments(args: dict):
    """Pull the relevant values out of the return values from the widgets."""
    # TODO: this now makes way too many assumptions, the config settings should
    # include instructions on how to combine widget return values when there are
    # more than one, for example, it should say something like "[#1(#2), #3]" to
    # replace the assumption now built into the third case below.
    processed_args = {}
    for arg, val in args.items():
        if len(val) == 1:
            processed_args[arg] = val[0]
        elif len(val) == 2:
            processed_args[arg] = val[0] if val[0] is not None else val[1]
        elif len(val) == 3:
            if val[0] is not None and val[1] is not None:
                processed_args[arg] = f'{val[0]}({val[1]})'
            else:
                processed_args[arg] = val[2]
    return processed_args

def import_session_objects(options: list):
    """Take the list of options intended for the selectbox and check for items that
    need to be expanded. At the moment, the only target is the string that indicates
    all blocks that are in play need to be inseted."""
    expanded_list = []
    for option in options:
        # if the option is a tuple then the first element is an instruction
        if isinstance(option, tuple):
            if option[0] == 'pool':
                # here the instruction is to retrieve objects from the pool
                expanded_list.extend(sorted(st.session_state.pool.get_in_play(option[1])))
        else:
            expanded_list.append(option)
    return expanded_list

def input_signature(input_description: dict):
    optionality_marker = '?' if input_description.get('optional') else ''
    return f'{input_description["type"]}{optionality_marker}'

'EOF'
