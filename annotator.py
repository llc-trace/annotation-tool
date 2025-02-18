"""

Timeline Annotator

Originally created for Action and Gesture annotation for the TRACE project.

To run this:

$ pip install -r requirements.txt
$ streamlit run annotator.py <VIDEO_FILE> <TASK_CONFIG>

"""


import json
import time

import streamlit as st

from config import default as config
import utils


DEBUG = True
DEBUG = False

st.set_page_config(page_title=config.TITLE, layout="wide")

utils.intialize_session_state()
video =  st.session_state.video


## SIDEBAR

# The sidebar prints some info, controls the annotation mode and shows video 
# controls and other controls

st.sidebar.title(config.TITLE)
utils.sidebar_display_info()
mode = utils.sidebar_display_tool_mode()
if 'annotation' in mode:
    offset, width = utils.sidebar_display_video_controls()
if mode == 'add annotations':
    add_settings = utils.sidebar_display_annotation_controls()
if mode == 'show annotations':
    list_settings = utils.sidebar_display_annotation_list_controls()
if mode == 'dev':
    dev = utils.sidebar_display_dev_controls()

if DEBUG:
    st.write(utils.session_options())


## MAIN CONTENT

if mode == 'add annotations':

    st.title('Add annotations')
    
    utils.display_video(video, width, offset.in_seconds())

    # The box with timeframe settings
    with st.container(border=True):
        t1, t2 = utils.display_timeframe_slider()
        tf = utils.create_timeframe_from_slider_inputs(t1, t2)
        if add_settings['tune-start']:
            utils.display_left_boundary(tf)
        if add_settings['tune-end']:
            utils.display_right_boundary(tf)

    # The box with the predicate and the argument structure
    with st.container(border=True):
        predicate = utils.display_predicate_selector(st)
        arguments = config.PREDICATES.get(predicate, [])
        args = utils.display_inputs(predicate, arguments)
        args = utils.process_arguments(args)

    # The box with the properties. But don't show it until after predicate
    # selection, which structures the annotation but also solved an issue
    # with refreshing the properties after an annotation was saved.
    if predicate:
        with st.container(border=True):
            properties = config.PROPERTIES
            props = utils.display_inputs(None, properties)
            props = utils.process_arguments(props)
    else:
        props = {}

    # Now that we have our values we can update the annotation
    annotation = st.session_state.annotation
    annotation.predicate = predicate
    annotation.arguments = args
    annotation.properties = props
    annotation.calculate_tier(tf)

    # Display the updated annotation with a save button or a warning    
    with st.container(border=True):
        utils.display_annotation(annotation, add_settings)
    if annotation.is_valid():
            st.button("Save Annotation", on_click=annotation.save)
    else:
        st.markdown(
            "*Cannot add annotation yet because not all required fields have"
            " been specified and/or not all values are legal.*")
        show_issues = st.button("Show issues")
        if show_issues:
            for e in annotation.errors:
                st.info(e)
    utils.display_errors()


if mode == 'show annotations':

    st.title('Annotations')
    if not list_settings['hide-video']:
        utils.display_video(video, width, offset.in_seconds())
    fname = st.session_state.io['json']
    if not list_settings['hide-controls']:
        with st.container(border=True):
            annotation_id = utils.display_remove_annotation_select()
            st.button('Remove', on_click=utils.action_remove_annotation, args=[annotation_id])
        st.button('Reload annotations', on_click=utils.load_annotations)
        reloaded = st.button('Reload annotations', on_click=utils.load_annotations)
        if reloaded:
            st.info('Annotations were reloaded')
    utils.display_messages()
    utils.display_annotations(list_settings)


if mode == 'show object pool':

    st.title('Blocks')
    st.text("Add blocks into play from the pool or remove them and put them back into the pool")
    messages = []
    c1, c2, _ = st.columns([4, 2, 6])
    #block_to_add = utils.display_add_block_select(c1)
    blocks_to_add = utils.display_add_block_select(c1)
    #c2.button("Add", on_click=utils.action_add_block, args=[block_to_add])
    c2.button("Add", on_click=utils.action_add_blocks, args=[blocks_to_add])
    c3, c4, _ = st.columns([4, 2, 6])
    block_to_remove = utils.display_remove_block_select(c3)
    c4.button("Remove", on_click=utils.action_remove_block, args=[block_to_remove])
    utils.display_messages()
    utils.display_available_blocks()


if mode == 'help':

    st.title('Annotation tool help')
    url = 'https://github.com/llc-trace/annotation-tool/blob/main/docs/manual/index.md'
    st.markdown(f'For help see the manual at [{url}]({url}).')


if mode == 'dev':

    st.title('Developer goodies')
    if dev['session_state']:
        with st.container(border=True):
            st.markdown('**Session State**')
            st.write(st.session_state)
    if dev['log']:
        with open(st.session_state.io['log']) as fh:
            with st.container(border=True):
                st.markdown('**Log contents**')
                st.code(fh.read(), language=None)
    if dev['predicate']:
        with st.container(border=True):
            st.markdown('**Predicate-argument specifications**')
            st.write(config.PREDICATES)
    if dev['properties']:
        with st.container(border=True):
            st.markdown('**Property specifications**')
            st.write(config.PROPERTIES)
