"""

TODO:
- Use second tier for actions if there is overlap
- Make sure that identifiers are unique
    now all is reset to 0 when restarting the tool
- Add reload and purge buttons on the show-annotations page?
✔︎ Update code to show images around boundaries
- Add more log messages
- deal with seconds/milliseconds < 0 after adjustement
- deal with out of bounds errors 
    both for seek function and for left and right adjust
- Make sure we avoid duplicate identifiers
    use utils.annotation_identifiers())
    also note that clicking "show elan" or "show json" the identifier
    of the current annotation changes
- Have the help page refer to the GitHub page?
- Figure out more precise way for sources and destinations
    use the propositions list for this
- Often when removing an annotation and doing it again the
    tool skips to "add annotations" mode
- Check whether using the data_editor widget makes sense
- Add a cache to the session state, it could contain all images that have
    so far been extracted

"""


import json
import time

import streamlit as st

import config
import utils


st.set_page_config(page_title="DPIP Action Annotator", layout="wide")

utils.intialize_session_state()
video =  st.session_state.video


## SIDEBAR

# The sidebar prints some info, controls the annotation mode and shows video 
# controls and other controls

st.sidebar.title('DPIP Action Annotation')
utils.sidebar_display_info()
mode = utils.sidebar_display_tool_mode()
if True or 'annotation' in mode:
    offset, width = utils.sidebar_display_video_controls()
if True or mode == 'add annotations':
    show = utils.sidebar_display_annotation_controls()


## MAIN CONTENT

if mode == 'add annotations':

    st.title('Add annotations')
    
    utils.display_video(video, width, offset.in_seconds())

    with st.container(border=True):
        t1, t2 = utils.display_timeframe_slider()
    tf = utils.create_timeframe_from_slider_inputs(t1, t2)

    if show['boundary']:
        with st.container(border=True):
            choice = st.pills(
                utils.create_label('Fine-tune boundaries'),
                ['adjust start point', 'adjust end point'], default='adjust start point')
            if choice == 'adjust start point':
                start_point = utils.display_left_boundary(tf)
            if choice == 'adjust end point':
                utils.display_right_boundary(tf)

    with st.container(border=True):
        predicate = utils.display_action_type_selector(st)
        action_args = config.ACTION_TYPES.get(predicate, [])
        args = utils.display_arguments(action_args)

    if 'annotation' not in st.session_state:
        st.session_state.annotation = \
            utils.ActionAnnotation(video.path, tf, predicate, args)
    annotation = st.session_state.annotation

    # Now that we have an annotation we can update the contents given the inputs
    annotation.predicate = predicate
    annotation.arguments = args
    annotation
    
    with st.container(border=True):
        utils.display_annotation(annotation, show)
        st.button("Add", on_click=annotation.save)

    utils.display_errors()

    if show['boundary']:
        # This is to make "Assertion fctx->async_lock" errors less likely,
        # much easier to do than the real fix which appears to be having
        # to do with threads. Two more of these were added to the utilities
        # when the problem came back due to added frames.
        time.sleep(1)

    #st.write(st.session_state)


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
