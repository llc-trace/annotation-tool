"""

DPIP Action Annotator

To run this:

$ pip install -r requirements.txt
$ streamlit run dpip_action_annotator.py <VIDEO_FILE>

"""


import json
import time

import streamlit as st

import config
import utils


DEBUG = True
DEBUG = False

st.set_page_config(page_title="DPIP Action Annotator", layout="wide")

utils.intialize_session_state()
video =  st.session_state.video


## SIDEBAR

# The sidebar prints some info, controls the annotation mode and shows video 
# controls and other controls

st.sidebar.title('DPIP Action Annotation')
utils.sidebar_display_info()
mode = utils.sidebar_display_tool_mode()
if 'annotation' in mode:
    offset, width = utils.sidebar_display_video_controls()
if mode == 'add annotations':
    show = utils.sidebar_display_annotation_controls()
if mode == 'dev':
    dev = utils.sidebar_display_dev_controls()

if DEBUG:
    st.write(utils.session_options())

# This is done here and not in utils.intialize_session_state() because
# the kind of annotation differens for actions and gestures.
if 'annotation' not in st.session_state:
    st.session_state.annotation = utils.ActionAnnotation()


## MAIN CONTENT


def current_timeframes():
    """Returns all timeframes of all the current annotations."""
    return [annotation.timeframe for annotation in st.session_state.annotations]

def calculate_tier(tf: utils.TimeFrame):
    taken = current_timeframes()
    #for tf in taken: st.write(tf)
    for taken_tf in taken:
        #print('   ', taken_tf, overlap(tf, taken_tf))
        if overlap(tf, taken_tf):
            return 'ACTION2'
    return 'ACTION1'

def overlap(tf1, tf2):
    if tf1.end <= tf2.start:
        return False
    if tf2.end <= tf1.start:
        return False
    return True


if mode == 'add annotations':

    st.title('Add annotations')
    
    utils.display_video(video, width, offset.in_seconds())

    with st.container(border=True):
        t1, t2 = utils.display_timeframe_slider()
    tf = utils.create_timeframe_from_slider_inputs(t1, t2)

    #t1, t2, st.session_state.opt_timeframe
    #st.session_state.annotation

    if show['tune-start']:
        with st.container(border=True):
            start_point = utils.display_left_boundary(tf)

    if show['tune-end']:
        with st.container(border=True):
            end_point = utils.display_right_boundary(tf)

    with st.container(border=True):
        #tier = st.selectbox(utils.create_label('Tier'), ('action-1', 'action-2'))
        predicate = utils.display_action_type_selector(st)
        action_args = config.ACTION_TYPES.get(predicate, [])
        args = utils.display_arguments(action_args)

    annotation = st.session_state.annotation
    
    # Now that we have an annotation we can update the contents given the inputs
    annotation.predicate = predicate
    annotation.arguments = args
    annotation.tier = calculate_tier(tf)
    
    if DEBUG:
        st.code(annotation.as_pretty_string(), language=None)

    with st.container(border=True):
        utils.display_annotation(annotation, show)
        st.button("Add", on_click=annotation.save)

    utils.display_errors()


if mode == 'show annotations':

    st.title('Annotations')
    utils.display_video(video, width, offset.in_seconds())
    fname = st.session_state.io['json']
    with st.container(border=True):
        annotation_id = utils.display_remove_annotation_select()
        st.button('Remove', on_click=utils.action_remove_annotation, args=[annotation_id])
    st.button('Reload annotations', on_click=utils.load_annotations)
    utils.display_messages()
    utils.display_annotations()


if mode == 'show blocks':

    st.title('Blocks')
    st.text("Add blocks into play from the pool or remove them and put them back into the pool")
    messages = []
    c1, c2, _ = st.columns([4, 2, 6])
    block_to_add = utils.display_add_block_select(c1)
    c2.button("Add", on_click=utils.action_add_block, args=[block_to_add])
    c3, c4, _ = st.columns([4, 2, 6])
    block_to_remove = utils.display_remove_block_select(c3)
    c4.button("Remove", on_click=utils.action_remove_block, args=[block_to_remove])
    utils.display_messages()
    utils.display_available_blocks()


if mode == 'help':

    with open('manual.md') as fh:
        st.markdown(fh.read())


if mode == 'dev':

    if dev['session_state']:
        with st.container(border=True):
            st.write(st.session_state)
    if dev['log']:
        with open(st.session_state.io['log']) as fh:
            with st.container(border=True):
                st.code(fh.read(), language=None)
