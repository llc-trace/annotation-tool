"""

Streamlit utilities.

Includes session state utilities, display utilities and action utilities.

"""

import os
import sys
import json
import datetime
import pathlib
import collections

import pandas as pd
import streamlit as st
import streamlit_timeline

from config import default as config
import util
from util.video import Video, TimePoint, TimeFrame, collect_frames
from util.annotation import Annotation, ObjectPool
from util.annotation import annotation_identifiers, load_annotations
from util.cache import ImageCache
from util import actions, components


# Session state utilities
# ----------------------------------------------------------------------------

def intialize_session_state():
    """The session state contains some controls as well as filenames for the output
    and the log, the current video, the object pool, the list of annotations, the
    current annotation, the image cash, the current errors and the current messages.
    """
    if 'errors' not in st.session_state:
        st.session_state.errors = []
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    options = util.get_command_line_options()
    video_path = options['video_path']
    config_path = options['config_path']
    debug = options['debug']
    st.session_state.debug = debug
    if 'io' not in st.session_state:
        basename = os.path.basename(video_path)
        if basename.endswith('.mp4'):
            basename = basename[:-4]
        st.session_state.io = {
            'video_path': video_path,
            'config_path': config_path,
            'json': f'data/{basename}.json',
            'elan': f'data/{basename}.tab',
            'log': f'data/{basename}.log'}
    if 'video' not in st.session_state:
        st.session_state.video = Video(video_path)
        util.log(f'Loaded video at {video_path}')
    if 'pool' not in st.session_state:
        st.session_state.pool = ObjectPool()
        for obj_type, objects in config.OBJECT_POOL.items():
            st.session_state.pool.add_objects(obj_type, objects)
    if 'annotations' not in st.session_state:
        load_annotations()
    if 'annotation' not in st.session_state:
        st.session_state.annotation = Annotation()
    if 'cache' not in st.session_state:
        st.session_state.cache = ImageCache()

def session_options():
    options = {}
    for var in st.session_state:
        if var.startswith('opt_'):
            options[var] = st.session_state[var]
    return options


# Display utilities
# ----------------------------------------------------------------------------

def text(key, value=None):
    return st.text_input(
        "dummy", key=key, value=value, label_visibility='collapsed')

def box(key, options):
    return st.selectbox(
        "dummy", [None] + options, key=key, label_visibility='collapsed')

def sidebar_display_info():
    text = (
        f'Task: "{config.TASK}"\n'
        + f'Annotations: {len(st.session_state.annotations)}')
    st.sidebar.code(text, language='yaml')

def sidebar_display_tool_mode():
    st.sidebar.header('Tool mode', divider=True)
    modes = ['add annotations', 'show annotations', 'show object pool', 'help', 'dev']
    return st.sidebar.radio(
        "Tool mode", modes, key='opt_mode', index=0, label_visibility='collapsed')

def sidebar_display_video_controls():
    st.sidebar.header('Video controls', divider=True)
    offset = sidebar_display_seek_inputs()
    st.sidebar.write(offset)
    width = sidebar_display_width_slider()
    return offset, width

def sidebar_display_seek_inputs():
    st.sidebar.markdown("Seek offset in video (hours, minutes, seconds)")
    col1, col2, col3, _ = st.sidebar.columns([4, 4, 5, 4])
    hours = col1.number_input('hh', min_value=0, label_visibility="collapsed")
    minutes = col2.number_input('mm', min_value=0, label_visibility="collapsed")
    seconds = col3.number_input('ss', min_value=0, label_visibility="collapsed")
    return TimePoint(
        hours=hours, minutes=minutes, seconds=seconds)

def sidebar_display_width_slider():
    return st.sidebar.slider(
        label=util.create_label("Width", size='small'),
        key='opt_video_width',
        min_value=25, max_value=100,
        value=config.DEFAULT_VIDEO_WIDTH, format="%d%%")

def sidebar_display_annotation_controls():
    st.sidebar.header('Annotation controls', divider=True)
    hide_boundaries = st.sidebar.checkbox('Hide boundary frames', key='opt_hide_boundaries')
    show_elan = st.sidebar.checkbox('Show ELAN', key='opt_show_elan')
    show_json = st.sidebar.checkbox('Show JSON', key='opt_show_json')
    return {
        'hide_boundaries': hide_boundaries,
        'elan': show_elan,
        'json': show_json }

def sidebar_display_annotation_list_controls():
    st.sidebar.header('Annotation list controls', divider=True)
    video = st.sidebar.checkbox('Hide video', key='opt_list_hide_video', value=True)
    timeline = st.sidebar.checkbox('Hide timeline', key='opt_list_hide_timeline')
    table = st.sidebar.checkbox('Hide table', key='opt_list_hide_table')
    return {
        'hide-video': video,
        'hide-timeline': timeline,
        'hide-table': table }

def sidebar_display_dev_controls():
    st.sidebar.header('Developer goodies', divider=True)
    options = ['Show session_state', 'Show config settings', 'Show log',
               'Show objects pool', 'Show predicate specifications',
               'Show property specifications', 'Show image cache', 'Show annotations']
    dev_option = st.sidebar.radio('dev_opt', options, label_visibility='collapsed')
    return dev_option

def display_video(video: 'Video', width: int, **kwargs):
    margin = max((100 - width), 0.01)
    container, _ = st.columns([width, margin])
    container.video(video.path, **kwargs)

def display_timeframe_slider():
    """Displays a slider with two timepoints and returns a pair of instances of
    datetime.time. The associated action named action_change_timeframe() sets the
    annotation's timeframe (with start and end timepoint) in the session state."""
    video = st.session_state.video
    slider = st.slider(label=util.create_label("Select timeframe"),
                       key='opt_timeframe',
                       value=(video.start, video.end),
                       max_value=video.end,
                       step=datetime.timedelta(seconds=1),
                       on_change=actions.change_timeframe,
                       format=config.SLIDER_TIME_FORMAT,
                       label_visibility='collapsed')
    return slider

def display_timepoint_tuner(label: str, tf: 'TimeFrame', tp: 'TimePoint'):
    step = datetime.timedelta(milliseconds=config.CONTEXT_STEP)
    margin = datetime.timedelta(seconds=config.FINE_TUNING_WINDOW)
    d = datetime.datetime(2020, 1, 1, tp.hours, tp.minutes, tp.seconds)
    with st.container(border=False):
        _, col, _ = st.columns([1, 30, 1])
        val = col.slider(
            util.create_label(label), d - margin, d + margin,
            value=d, format=config.SLIDER_TIME_FORMAT, step=step)
        return val

def display_tier():
    st.write('**Tier**')
    return st.selectbox(
        'select-tier', [None] + config.TIERS, label_visibility='collapsed')

def display_arguments(predicate: str, inputs: list, conjunct=False):
    # The inputs argument is a list of dictionaries, where each dictionary
    # contains the specification for an argument or property.
    args = {}
    descriptions = [util.input_signature(d) for d in inputs]
    d = f'{predicate} ( {", ".join(descriptions)})'
    st.info(d)
    if inputs:
        display_inputs_helper(inputs, args, conjunct)
    return args

def display_properties(inputs: list):
    # The inputs argument is a list of dictionaries, where each dictionary
    # contains the specification for a property.
    props = {}
    descriptions = [util.input_signature(d) for d in inputs]
    d = f'{", ".join(descriptions)})'
    if inputs:
        display_inputs_helper(inputs, props)
    return props

def display_inputs_helper(inputs: list, inputs_dict: dict, conjunct=False):
    """This is a helper for both the display_arguments() and display_properties()
    functions, it prints th einput fields and collects the settings in the input
    dictionary."""
    # TODO: this may break when a property name is the same as an argument name so
    # may need to do something better to make sure that keys are unique.
    prefix = 'c-' if conjunct else ''
    args = [''] * len(inputs)
    for i, arg in enumerate(inputs):
        atype = arg['type']
        label = arg['label']
        items = arg['items']
        st.write(label)
        args[i] = [None] * len(items)
        cols = st.columns(len(items))
        for j, item in enumerate(items):
            if item == 'TEXT':
                with cols[j]:
                    args[i][j] = text(f'{prefix}{i}:{j}-{atype}')
            elif isinstance(item, str):
                with cols[j]:
                    args[i][j] = text(f'{prefix}{i}:{j}-{atype}', item)
            elif isinstance(item, list):
                item = util.import_session_objects(item)
                with cols[j]:
                    args[i][j] = box(f'{prefix}{i}:{j}-{atype}', item)
        inputs_dict[atype] = args[i]

def display_annotation(annotation, show_options: dict):
    st.markdown('###### Current values')
    df = pd.DataFrame([annotation.as_row()], columns=annotation.columns())
    st.table(df)
    if show_options['elan']:
        st.code(annotation.as_elan())
    if show_options['json']:
        with st.container(border=True):
            st.json(annotation.as_json())

def display_annotations(settings: dict):
    annotations = util.get_annotations()
    with st.container(border=True):
        st.text('Select a range to display')
        t1, t2 = display_timeframe_slider()
        annotations = util.get_annotations_in_range(annotations, t1, t2)
        term = st.text_input('Search annotations')
        filtered_annotations = [a for a in annotations if a.matches(term)]
    if not settings['hide-timeline']:
        display_annotations_timeline(filtered_annotations)
    if not settings['hide-table']:
        with st.container(border=True):
            display_annotations_table(sorted(filtered_annotations))

# TODO: this needs to move to components
def display_annotations_timeline(annotations: list):
    def annotation_pp(anno: dict):
        if anno is None:
            return None
        annotation = Annotation.from_dictionary(anno)
        st.code(annotation.as_yaml(), language='yaml')
        #st.json(annotation.as_json())
        offsets = list(range(annotation.start, annotation.end, 500))
        frames = collect_frames(st.session_state.video, offsets[:10])
        components.video_frames_from_list(frames)
    tiers = sorted(set([a.tier for a in annotations if a.tier]))
    groups = [{"id": tier, "content": tier.lower()} for tier in tiers]
    # Arrived at these numbers experimentally, the height of a tier is 1.3 cm on the
    # screen and the timeline at the bottom is 1.8 cm. The 42 is a multiplier to get
    # to an agreeable number of pixels.
    height = ((len(tiers) * 1.3) + 1.8) * 42
    options = { "selectable": True, "zoomable": True, "stack": False, "height": height }
    timeline_items = util.get_timeline(annotations)
    try:
        selected_item = streamlit_timeline.st_timeline(
            timeline_items, groups=groups, options=options)
    except Exception as e:
        st.warning('Could not display the timeline')
        util.error('Could not display the timeline', body=str(e))
        selected_item = None
    if selected_item:
        with st.container(border=True):
            st.text('Selected annotation')
            annotation_pp(selected_item['annotation'])
            start = max(int(selected_item['annotation']['start'] / 1000) - 1, 0)
            end = int(selected_item['annotation']['end'] / 1000) + 1
            play = st.button(f"Play annotation")
            if play:
                try:
                    display_video(
                        st.session_state.video, 50, start_time=start, end_time=end,
                        loop=True, autoplay=True)
                    st.button(f"Stop playing")
                except Exception as e:
                    st.warning(f'Error playing video: {e}')

def get_chunks(items: list, n: int):
    return [items[i:i + n] for i in range(0, len(items), n)]

def display_annotations_table(annotations: list):
    def as_row(annotation):
        # does not include task, tier and properties fields
        return annotation.as_row()[2:-1]
    structured_annotations = collections.defaultdict(dict)
    for a in annotations:
        structured_annotations[a.task].setdefault(a.tier, []).append(a)
    columns = Annotation.columns()[2:-1]
    for task in sorted(structured_annotations):
        for tier in sorted(structured_annotations[task]):
            # st.markdown(f'##### {task} &longrightarrow; {tier}')
            st.code(f'task: "{task}"\ntier: "{tier}"', language='yaml')
            rows = [as_row(a) for a in structured_annotations[task][tier]]
            st.table(pd.DataFrame(rows, columns=columns))

def display_errors():
    for error in st.session_state.errors:
        st.error(error)
    st.session_state.errors = []

def display_messages():
    for message in st.session_state.messages:
        st.info(message)
    st.session_state.messages = []

def display_available_objects(obj_type: str):
    st.info(f'**Currently available {obj_type}**')
    objs = list(sorted(st.session_state.pool.objects[obj_type]['inplay']))
    with st.container(border=True):
        st.text('\n'.join(objs))

def display_remove_annotation_select():
    return st.selectbox('Remove annotation', [None] + annotation_identifiers())
