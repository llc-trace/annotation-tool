"""

Streamlit utilities.

Includes session state utilities, display utilities and action utilities.

"""

import os
import sys
import json
import datetime
import pathlib

import pandas as pd
import streamlit as st
import streamlit_timeline

from config import default as config
import util
from util.video import Video, TimePoint, TimeFrame, collect_frames
from util.annotation import Annotation, ObjectPool
from util.annotation import annotation_identifiers, load_annotations
from util.cache import ImageCache


# Session state utilities
# ----------------------------------------------------------------------------

def intialize_session_state():
    """The session state contains some controls as well as filenames for the output
    and the log, the current video, the object pool, the list of annotations, the
    current annotation, the image cash, the current errors and the current messages.
    """
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
    if 'errors' not in st.session_state:
        st.session_state.errors = []
    if 'messages' not in st.session_state:
        st.session_state.messages = []

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
    controls = st.sidebar.checkbox('Hide controls', key='opt_list_hide_controls', value=False)
    timeline = st.sidebar.checkbox('Hide timeline', key='opt_list_hide_timeline')
    table = st.sidebar.checkbox('Hide table', key='opt_list_hide_table')
    return {
        'hide-video': video,
        'hide-controls': controls,
        'hide-timeline': timeline,
        'hide-table': table }

def sidebar_display_dev_controls():
    st.sidebar.header('Developer goodies', divider=True)
    options = ['Show session_state', 'Show config settings', 'Show log',
               'Show objects pool', 'Show predicate specifications',
               'Show property specifications', 'Show image cache']
    dev_option = st.sidebar.radio('dev_opt', options, label_visibility='collapsed')
    return dev_option

def display_video(video: 'Video', width: int, print_info=True, **kwargs):
    if print_info:
        st.info(video.filename)
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
                       on_change=action_change_timeframe,
                       format=config.SLIDER_TIME_FORMAT)
    return slider

def display_capture_boundaries():
    st.markdown('**Select start and end in hh:mm:ss:mmm**')
    keys1 = ['start_hh', 'start_mm', 'start_ss', 'start_mmm']
    keys2 = ['end_hh', 'end_mm', 'end_ss', 'end_mmm']
    col1, col2 = st.columns(2)
    with col1:
        tp1 = display_seek_inputs('Start', keys=keys1)
        st.write(tp1)
    with col2:
        tp2 = display_seek_inputs('End', keys=keys2)
        st.write(tp2)
    # Trap out of bounds errors
    video_length = len(st.session_state.video)
    if tp2.in_seconds() > video_length:
        end = st.session_state.video.get_video_end()
        tp2 = TimePoint.from_time(end)
        st.warning(
            'Warning: out-of-bounds error for the endpoint, '
            f'using "{tp2.timestamp(short=True)}" instead')
    tf = TimeFrame(start=tp1, end=tp2, video=st.session_state.video)
    st.session_state.annotation.timeframe = tf
    return tf

def display_seek_inputs(header: str, keys: list):
    # TODO: this is similar to sidebar_display_seek_inputs(), those two should
    # be combined
    def get_number(column, label: str, key: str):
        return column.number_input(
            label, key=key, min_value=0, label_visibility="collapsed")
    col0, col1, col2, col3, col4, _ = st.columns([3, 4, 4, 4, 4, 6])
    col0.markdown(header)
    hours = get_number(col1, 'hh', keys[0])
    minutes = get_number(col2, 'ss', keys[1])
    seconds = get_number(col3, 'mm', keys[2])
    mseconds = get_number(col4, 'mmm', keys[3])
    return TimePoint(
        hours=hours, minutes=minutes, seconds=seconds, milliseconds=mseconds)

def display_left_boundary(timeframe: 'TimeFrame'):
    #st.write('**Showing left boundary**')
    ms = timeframe.start.in_milliseconds()
    timepoint = TimePoint(milliseconds=ms)
    frames = collect_frames(timeframe.video, util.get_window(ms))
    display_sliding_window(st, frames, timepoint)

def display_right_boundary(timeframe: 'TimeFrame'):
    #st.write('**Showing right boundary**')
    ms = timeframe.end.in_milliseconds()
    timepoint = TimePoint(milliseconds=ms)
    frames = collect_frames(timeframe.video, util.get_window(ms))
    display_sliding_window(st, frames, timepoint)

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

def display_sliding_window(column, frames, tp, header=None):
    """Display frames horizontally in a box."""
    with column.container(border=False):
        if header is not None:
            column.write(header)
        cols = column.columns(len(frames))
        for i, frame in enumerate(frames):
            is_focus = False
            if tp.in_milliseconds() == frame.timepoint.in_milliseconds():
                is_focus = True
            display_frame(cols[i], frame, focus=is_focus)

def display_frames(column, frames, cols=10, header=None):
    """Display frames horizontally in a box."""
    box = column.container(border=True)
    if header is not None:
        box.write(header)
    cols = box.columns(cols)
    for i, frame in enumerate(frames):
        display_frame(cols[i], frame)

def display_frame(column, frame, focus=False):
    caption = f'✔︎' if focus else frame.caption()
    if frame.success:
        column.image(frame.image, channels="BGR", caption=caption)
    # TODO: on failure may want to pass in an empty image with a caption like
    # below, but before that need to figure out how to control the size of the
    # image better (that is make it match the video screen dimensions).
    # svg = (
    #     '<svg width="100" height="75" xmlns="http://www.w3.org/2000/svg">'
    #     '<rect width="100" height="75" /></svg>')
    # column.image(svg, caption=caption)

def display_tier():
    st.write('**Tier**')
    return st.selectbox(
        'select-tier', [None] + config.TIERS, label_visibility='collapsed')

def display_inputs(predicate: str, inputs: list):
    # The inputs argument is a list of dictionaries, where each dictionary
    # contains the specification for an argument or property.
    inputs_dict = {}
    if predicate is not None:
        descriptions = [util.input_signature(d) for d in inputs]
        d = f'{predicate} ( {", ".join(descriptions)})'
        st.info(d)
    if inputs:
        args = [''] * len(inputs)
        for i, arg in enumerate(inputs):
            type = arg['type']
            label = arg['label']
            items = arg['items']
            st.write(label)
            args[i] = [None] * len(items)
            cols = st.columns(len(items))
            for j, item in enumerate(items):
                if item == 'TEXT':
                    with cols[j]:
                        args[i][j] = text(f'{i}:{j}-{type}')
                elif isinstance(item, str):
                    with cols[j]:
                        args[i][j] = text(f'{i}:{j}-{type}', item)
                elif isinstance(item, list):
                    item = util.import_session_objects(item)
                    with cols[j]:
                        args[i][j] = box(f'{i}:{j}-{type}', item)
            inputs_dict[type] = args[i]
    return inputs_dict

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
    with st.container(border=True):
        term = st.text_input('Search annotations')
        filtered_annotations = \
            [a for a in reversed(st.session_state.annotations) if a.matches(term)]
        if not settings['hide-timeline']:
            display_annotations_timeline(filtered_annotations)
        if not settings['hide-table']:
            display_annotations_table(sorted(filtered_annotations))

def display_annotations_timeline(annotations: list):
    def annotation_pp(anno: dict):
        if anno is None:
            return None
        annotation = Annotation().import_fields(anno)
        st.write(annotation)
        offsets = list(range(annotation.start, annotation.end, 500))
        frames = collect_frames(st.session_state.video, offsets[:10])
        display_frames(st, frames, cols=10)
    tiers = sorted(set([a.tier for a in annotations if a.tier]))
    groups = [{"id": tier, "content": tier.lower()} for tier in tiers]
    # Arrived at these numbers experimentally, the height of a tier is 1.3 cm on the
    # screen and the timeline at the bottom is 1.8 cm. The 42 is a multiplier to get
    # to an agreeable number of pixels.
    height = ((len(tiers) * 1.3) + 1.8) * 42
    options = { "selectable": True, "zoomable": True, "stack": False, "height": height }
    timeline_items = util.get_timeline(annotations)
    try:
        item = streamlit_timeline.st_timeline(timeline_items, groups=groups, options=options)
        if item:
            annotation_pp(item['annotation'])
    except Exception:
        pass

def display_annotations_table(annotations: list):
    rows = [a.as_row() for a in annotations]
    st.table(pd.DataFrame(rows, columns=Annotation.columns()))

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

def display_predicate_selector(column, key='action_type'):
    label = util.create_label('Select predicate')
    return st.pills(label, config.PREDICATES.keys(), key=key)

def display_remove_annotation_select():
    return st.selectbox('Remove annotation', [None] + annotation_identifiers())


# Actions
# ----------------------------------------------------------------------------

def action_clear_image_cache():
    st.session_state.cache.reset()

def action_change_timeframe():
    t1, t2 = st.session_state.opt_timeframe
    if st.session_state.annotation.timeframe is None:
        st.session_state.annotation.timeframe = TimeFrame()
    st.session_state.annotation.timeframe.start = TimePoint.from_time(t1)
    st.session_state.annotation.timeframe.end = TimePoint.from_time(t2)

def action_add_objects(object_type: str, objects: list):
    """Put the objects in the list in play, that is, move them from the 'available'
    bin to the 'inplay' bin. After this, they will be available as options."""
    st.session_state.pool.put_objects_in_play(object_type, objects)
    with open(st.session_state.io['json'], 'a') as fh:
        for obj in objects:
            fh.write(json.dumps({"add-object": (object_type, obj)}) + '\n')
            message = f'Added {obj} and removed it from the pool'
            st.session_state.messages.append(message)
            util.log(message)

def action_remove_objects(object_type: str, objects: list):
    """Remove the objects in the list from play, that is, move them from the 'inplay'
    bin to the 'available' bin. After this, they won't be available as options."""
    st.session_state.pool.remove_objects_from_play(object_type, objects)
    with open(st.session_state.io['json'], 'a') as fh:
        for obj in objects:
            fh.write(json.dumps({"remove-object": (object_type, obj)}) + '\n')
            message = f'Removed {obj} and returned it to the pool'
            st.session_state.messages.append(message)
            util.log(message)

def action_remove_annotation(annotation_id: str):
    if annotation_id is not None:
        with open(st.session_state.io['json'], 'a') as fh:
            fh.write(json.dumps({"remove-annotation": annotation_id}) + '\n')
        remove_annotation(annotation_id)
        message = f"Removed  annotation {annotation_id}"
        st.session_state.messages.append(message)
        util.log(message)

def action_save_starting_time(timepoint: 'TimePoint'):
    st.session_state.annotation.timeframe.start = timepoint
    st.session_state.opt_tune_start = False
    util.log(f'Saved starting time {timepoint}')

def action_save_ending_time(timepoint: 'TimePoint'):
    st.session_state.annotation.timeframe.end = timepoint
    st.session_state.opt_tune_end = False
    util.log(f'Saved ending time {timepoint}')

def remove_annotation(annotation_id: str):
    st.session_state.annotations = \
        [a for a in st.session_state.annotations if a.identifier != annotation_id]

'EOF'