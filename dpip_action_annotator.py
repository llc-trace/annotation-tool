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

video_path = utils.get_video_location_from_command_line()
utils.st_intialize_session_state(st, video_path)
video =  st.session_state.video

# The sidebar controls the timepoint in the video, the number of thumbnails, and
# the width of the video
st.sidebar.markdown('# DPIP Action Annotation')
st.sidebar.text(
    f'Number of blocks: {len(st.session_state.objects["inplay"])}\n'
    + f'Number of annotations: {len(st.session_state.annotations)}\n'
    + f'Lenght of video in seconds: {len(video)}')
offset = utils.st_sidebar_seek(st)
width = utils.st_sidebar_width_slider(st)
st.sidebar.markdown('### Tool mode')
mode = st.sidebar.radio(
    "Tool mode",
    ['add annotations', 'show annotations', 'show objects', 'help'],
    label_visibility='collapsed')
st.sidebar.markdown('### Optional inputs')
show_boundaries = st.sidebar.checkbox('Show boundaries')

# displays the video title and the video itself
if not mode in ('show objects', 'help'):
    utils.display_video(video_path, width, offset.in_seconds(), st)


if mode == 'add annotations':

    st.markdown('### Add annotations')
    t1, t2 = utils.display_timeframe_slider(st, video)
    tf = utils.TimeFrame(
        utils.TimePoint(hours=t1.hour, minutes=t1.minute, seconds=t1.second),
        utils.TimePoint(hours=t2.hour, minutes=t2.minute, seconds=t2.second))

    if show_boundaries:
        adjust_start_col, adjust_end_col, _ = st.columns([1,1,4])
        adjust_start = adjust_start_col.number_input('adjust_left', value=0)
        adjust_end = adjust_end_col.number_input('adjust_right', value=0)
        tf.adjust(adjust_start, adjust_end)
        utils.display_images(tf, 4, st)
        # this is to make "Assertion fctx->async_lock" errors less likely
        time.sleep(1)

    action_column, argument_column = st.columns([3,8])
    with action_column:
        action_type = utils.display_action_type_selector(action_column)
    with argument_column:
        action_args = config.ACTION_TYPES.get(action_type, [])
        args = utils.display_arguments(action_args, st)

    annotation = utils.ActionAnnotation(
        video_path, tf.start.in_seconds(), tf.end.in_seconds(), action_type, args)
    st.code(annotation.as_elan())
    st.json(annotation.as_json())

    # the streamlit instance is handed in for the session state
    st.button("Add Action Annotation", on_click=annotation.save, args=[st])

    utils.display_errors(st)


if mode == 'show annotations':

    fname = st.session_state.io['json']
    st.markdown('### Annotations')
    #st.button("Load Annotations", on_click=utils.load_annotations, args=[st])

    utils.display_annotations(st)


if mode == 'show objects':

    st.markdown('### Objects')
    st.text("Add blocks into play from the pool or remove them and put them back into the pool")
    messages = []
    c1, c2, _ = st.columns([4, 2, 6])
    block_to_add = utils.display_add_block_select(st, c1)
    c2.button("Add", on_click=utils.action_add_block,
                            args=[block_to_add, messages, st])
    c3, c4, _ = st.columns([4, 2, 6])
    block_to_remove = utils.display_remove_block_select(st, c3)
    c4.button("Remove", on_click=utils.action_remove_block,
                               args=[block_to_remove, messages, st])
    utils.display_messages(messages, st)
    utils.display_available_blocks(st)


if mode == 'help':

    with open('manual.md') as fh:
        st.markdown(fh.read())
