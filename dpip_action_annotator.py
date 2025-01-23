"""

TODO:
✔︎ Use Elan-like identifier for elan export
✔︎ Confirm elan identifier does not have to be unique
- Use second tier for actions if there is overlap
✔︎ Add data directory for saving the annotations
✔︎ Use pulldown for object selection
✔︎ Load existing annotations when starting the tool
- Add reload and purge buttons on the show-annotations page?
- Add functionality to delete annotations
✔︎ Update code to show images around boundaries
✔︎ Add specifications on adding/removing blocks to the JSON file
✔︎ Add a log
- Make sure we avoid duplicate identifiers
    use utils.annotation_identifiers())
- Have the help page refer to the GitHub page?
- Figure out more precise way for sources and destinations
    use the propositions list for this

"""


import json
import time

import streamlit as st

import config
import utils


st.set_page_config(page_title="DPIP Action Annotator", layout="wide")

utils.intialize_session_state()
video =  st.session_state.video

# The sidebar controls the timepoint in the video, the number of thumbnails, and
# the width of the video
st.sidebar.markdown('# DPIP Action Annotation')
st.sidebar.text(
    f'Number of blocks: {len(st.session_state.objects["inplay"])}\n'
    + f'Number of annotations: {len(st.session_state.annotations)}\n'
    + f'Lenght of video in seconds: {len(video)}')
offset = utils.display_sidebar_seek_inputs()
width = utils.display_sidebar_width_slider()
st.sidebar.markdown('### Tool mode')
mode = st.sidebar.radio(
    "Tool mode",
    ['add annotations', 'show annotations', 'show objects', 'help'],
    label_visibility='collapsed')
st.sidebar.markdown('### Optional inputs')
show_boundaries = st.sidebar.checkbox('Show boundaries')

# displays the video title and the video itself
if not mode in ('show objects', 'help'):
    utils.display_video(video.path, width, offset.in_seconds())


if mode == 'add annotations':

    st.markdown('### Add annotations')
    t1, t2 = utils.display_timeframe_slider()
    tf = utils.TimeFrame(
        utils.TimePoint(hours=t1.hour, minutes=t1.minute, seconds=t1.second),
        utils.TimePoint(hours=t2.hour, minutes=t2.minute, seconds=t2.second))

    if show_boundaries:
        adjust_start_col, adjust_end_col, _ = st.columns([1,1,4])
        adjust_start = adjust_start_col.number_input('adjust_left', value=0)
        adjust_end = adjust_end_col.number_input('adjust_right', value=0)
        tf.adjust(adjust_start, adjust_end)
        utils.display_images(tf)
        # this is to make "Assertion fctx->async_lock" errors less likely
        time.sleep(1)

    action_column, argument_column = st.columns([3,8])
    with action_column:
        action_type = utils.display_action_type_selector(action_column)
    with argument_column:
        action_args = config.ACTION_TYPES.get(action_type, [])
        args = utils.display_arguments(action_args)

    annotation = utils.ActionAnnotation(video.path, tf, action_type, args)
    utils.display_annotation(annotation)

    # the streamlit instance is handed in for the session state
    st.button("Add Action Annotation", on_click=annotation.save)

    utils.display_errors()


if mode == 'show annotations':

    st.markdown('### Annotations')
    fname = st.session_state.io['json']
    annotation_id = utils.display_remove_annotation_select()
    st.button('Remove', on_click=utils.action_remove_annotation, args=[annotation_id])
    utils.display_annotations()


if mode == 'show objects':

    st.markdown('### Objects')
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
