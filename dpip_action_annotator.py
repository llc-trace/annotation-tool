"""

DPIP Action Annotator

To run this:

$ pip install -r requirements.txt
$ streamlit run dpip_action_annotator.py <VIDEO_FILE>

"""


import json
import time

import streamlit as st
from streamlit_timeline import st_timeline

import config
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

# This is done here and not in utils.intialize_session_state() because
# the kind of annotation differens for actions and gestures.
if 'annotation' not in st.session_state:
    st.session_state.annotation = utils.ActionAnnotation()



def display_action_type_selector(column, key='action_type'):
    label = utils.create_label('Select action type')
    return st.pills(label, config.PREDICATES.keys(), key=key)


def display_arguments(arguments: list):
    def text(key, value=None):
        return st.text_input(
            "dummy", key=key, value=value, label_visibility='collapsed')
    def box(key, options):
        return st.selectbox(
            "dummy", [None] + options, key=key, label_visibility='collapsed')
    arg_dict = {}
    if arguments:
        args = [''] * len(arguments)
        for i, arg in enumerate(arguments):
            argtype = arg['type']
            label = arg['label']
            items = arg['items']
            st.write(label)
            args[i] = [None] * len(items)
            cols = st.columns(len(items))
            for j, item in enumerate(items):
                if item == 'TEXT':
                    with cols[j]:
                        args[i][j] = text(f'{i}:{j}-{argtype}')
                elif isinstance(item, str):
                    with cols[j]:
                        args[i][j] = text(f'{i}:{j}-{argtype}', item)
                elif isinstance(item, list):
                    item = import_session_objects(item)
                    with cols[j]:
                        args[i][j] = box(f'{i}:{j}-{argtype}', item) 
            arg_dict[argtype] = args[i]
    return arg_dict


def import_session_objects(options: list):
    """Take the list of options intended for the selectbox and check for items that
    need to be expanded. At the moment, the only target is the string that indicates
    all blocks that are in play need to be inseted."""
    expanded_list = []
    for option in options:
        if option == '**session_state:blocks**':
            # sort the blocks because it is a set
            expanded_list.extend(sorted(st.session_state.objects['inplay']))
        else:
            expanded_list.append(option)
    return expanded_list


def process_arguments(args):
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



## MAIN CONTENT

if mode == 'add annotations':

    st.title('Add annotations')
    
    utils.display_video(video, width, offset.in_seconds())

    with st.container(border=True):
        t1, t2 = utils.display_timeframe_slider()
    tf = utils.create_timeframe_from_slider_inputs(t1, t2)

    if add_settings['tune-start']:
        with st.container(border=True):
            start_point = utils.display_left_boundary(tf)

    if add_settings['tune-end']:
        with st.container(border=True):
            end_point = utils.display_right_boundary(tf)

    with st.container(border=True):
        predicate = display_action_type_selector(st)
        action_args = config.PREDICATES.get(predicate, [])
        args = display_arguments(action_args)
        args = process_arguments(args)
    
    annotation = st.session_state.annotation
    
    # Now that we have an annotation we can update the contents given the inputs
    annotation.predicate = predicate
    annotation.arguments = args
    annotation.tier = utils.calculate_tier(tf)
    
    if DEBUG:
        st.code(annotation.as_pretty_string(), language=None)

    with st.container(border=True):
        #st.markdown(annotation.as_markdown())
        utils.display_annotation(annotation, add_settings)
        st.button("Add", on_click=annotation.save)

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
    utils.display_messages()
    utils.display_annotations(list_settings)


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
