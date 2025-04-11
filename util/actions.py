"""

Actions used by the streamlit applications.

"""

import json

import streamlit as st

import util
from util.video import TimePoint, TimeFrame


def clear_image_cache():
    st.session_state.cache.reset()

def change_timeframe():
    t1, t2 = st.session_state.opt_timeframe
    if st.session_state.annotation.timeframe is None:
        st.session_state.annotation.timeframe = TimeFrame()
    st.session_state.annotation.timeframe.start = TimePoint.from_time(t1)
    st.session_state.annotation.timeframe.end = TimePoint.from_time(t2)

def add_objects(object_type: str, objects: list):
    """Put the objects in the list in play, that is, move them from the 'available'
    bin to the 'inplay' bin. After this, they will be available as options."""
    st.session_state.pool.put_objects_in_play(object_type, objects)
    with open(st.session_state.io['json'], 'a') as fh:
        for obj in objects:
            fh.write(json.dumps({"add-object": (object_type, obj)}) + '\n')
            message = f'Added {obj} and removed it from the pool'
            st.session_state.messages.append(message)
            util.log(message)

def remove_objects(object_type: str, objects: list):
    """Remove the objects in the list from play, that is, move them from the 'inplay'
    bin to the 'available' bin. After this, they won't be available as options."""
    st.session_state.pool.remove_objects_from_play(object_type, objects)
    with open(st.session_state.io['json'], 'a') as fh:
        for obj in objects:
            fh.write(json.dumps({"remove-object": (object_type, obj)}) + '\n')
            message = f'Removed {obj} and returned it to the pool'
            st.session_state.messages.append(message)
            util.log(message)

def remove_annotation(annotation_id: str):
    if annotation_id is not None:
        with open(st.session_state.io['json'], 'a') as fh:
            fh.write(json.dumps({"remove-annotation": annotation_id}) + '\n')
        remove_annotation(annotation_id)
        message = f"Removed  annotation {annotation_id}"
        st.session_state.messages.append(message)
        util.log(message)

def save_starting_time(timepoint: 'TimePoint'):
    st.session_state.annotation.timeframe.start = timepoint
    st.session_state.opt_tune_start = False
    util.log(f'Saved starting time {timepoint}')

def save_ending_time(timepoint: 'TimePoint'):
    st.session_state.annotation.timeframe.end = timepoint
    st.session_state.opt_tune_end = False
    util.log(f'Saved ending time {timepoint}')

def remove_annotation(annotation_id: str):
    st.session_state.annotations = \
        [a for a in st.session_state.annotations if a.identifier != annotation_id]
