"""

Utilities for the annotator

"""


import os
import sys
import json
import time
import datetime
import pathlib
import functools
from copy import deepcopy

import cv2
import pandas as pd
import streamlit as st
import streamlit_timeline

from config import default as config
from util.cache import ImageCache


## Streamlit utilities
## ----------------------------------------------------------------------------

def text(key, value=None):
    return st.text_input(
        "dummy", key=key, value=value, label_visibility='collapsed')

def box(key, options):
    return st.selectbox(
        "dummy", [None] + options, key=key, label_visibility='collapsed')

def intialize_session_state():
    """The session state contains some controls as well as filenames for the output
    and the log, the current video, the object pool, the list of annoations, the
    current annotation, the image cash, the current errors and the current messages.
    """
    video_path = get_video_location_from_command_line()
    if not 'io' in st.session_state:
        basename = os.path.basename(video_path)
        if basename.endswith('.mp4'):
            basename = basename[:-4]
        st.session_state.io = {
            'json': f'data/{basename}.json',
            'elan': f'data/{basename}.tab',
            'log': f'data/{basename}.log'}
    if not 'video' in st.session_state:
        st.session_state.video = Video(video_path)
        log(f'Loaded video at {video_path}')
    if not 'pool' in st.session_state:
        st.session_state.pool = ObjectPool()
        for obj_type, objects in config.OBJECT_POOL.items():
            st.session_state.pool.add_objects(obj_type, objects)
    if not 'annotations' in st.session_state:
        load_annotations()
    if 'annotation' not in st.session_state:
        st.session_state.annotation = Annotation()
    if not 'cache' in st.session_state:
        st.session_state.cache = ImageCache()
    if not 'errors' in st.session_state:
        st.session_state.errors = []
    if not 'messages' in st.session_state:
        st.session_state.messages = []

def session_options():
    options = {}
    for var in st.session_state:
        if var.startswith('opt_'):
            options[var] = st.session_state[var]
    return options

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
    st.sidebar.markdown("Seek offset in video (hours, minutes, seconds, milliseconds)")
    col1, col2, col3, col4, _ = st.sidebar.columns([4,4,4,6,4])
    hours = col1.number_input('hh', min_value=0, label_visibility="collapsed")
    minutes = col2.number_input('mm', min_value=0, label_visibility="collapsed")
    seconds = col3.number_input('ss', min_value=0, label_visibility="collapsed")
    mseconds = col4.number_input('mmm', min_value=0, label_visibility="collapsed")
    return TimePoint(
        hours=hours, minutes=minutes, seconds=seconds, milliseconds=mseconds)

def sidebar_display_width_slider():
    return st.sidebar.slider(
        label=create_label("Width", size='small'),
        key='opt_video_width',
        min_value=25, max_value=100,
        value=config.DEFAULT_VIDEO_WIDTH, format="%d%%")

def sidebar_display_annotation_controls():
    st.sidebar.header('Annotation controls', divider=True)
    tune_start = st.sidebar.checkbox('Fine-tune start point', key='opt_tune_start')
    tune_end = st.sidebar.checkbox('Fine-tune end point', key='opt_tune_end')
    show_elan = st.sidebar.checkbox('Show ELAN', key='opt_show_elan')
    show_json = st.sidebar.checkbox('Show JSON',  key='opt_show_json')
    return {
        'tune-start': tune_start,
        'tune-end': tune_end,
        'elan': show_elan,
        'json': show_json }

def sidebar_display_annotation_list_controls():
    st.sidebar.header('Annotation list controls', divider=True)
    video = st.sidebar.checkbox('Hide video',  key='opt_list_hide_video', value=True)
    controls = st.sidebar.checkbox('Hide controls',  key='opt_list_hide_controls', value=True)
    timeline = st.sidebar.checkbox('Hide timeline',  key='opt_list_hide_timeline')
    table = st.sidebar.checkbox('Hide table',  key='opt_list_hide_table')
    return {
        'hide-video': video,
        'hide-controls': controls,
        'hide-timeline': timeline,
        'hide-table': table }

def sidebar_display_dev_controls():
    st.sidebar.header('Developer goodies', divider=True)
    dev_session = st.sidebar.checkbox('Show session_state', value=False)
    dev_pool = st.sidebar.checkbox('Show objects pool', value=False)
    dev_log = st.sidebar.checkbox('Show log', value=False)
    dev_pred = st.sidebar.checkbox('Show predicate specifications', value=False)
    dev_props = st.sidebar.checkbox('Show property specifications', value=False)
    dev_cache = st.sidebar.checkbox('Show image cache', value=False)
    return {
        'session_state': dev_session,
        'pool': dev_pool,
        'log': dev_log,
        'predicate': dev_pred,
        'properties':dev_props,
        'cache': dev_cache
        }

def display_video(video: 'Video', width, seconds):
    st.info(video.filename)
    margin = max((100 - width), 0.01)
    container, _ = st.columns([width, margin])
    container.video(video.path, start_time=seconds)

def display_timeframe_slider():
    """Displays a slider with two timepoints and returns a pair of instances of
    datetime.time. The associated action named action_change_timeframe() sets the
    annotation's timeframe (with start and end timepoint) in the session state."""
    video = st.session_state.video
    return st.slider(label=create_label("Select timeframe"),
                     key='opt_timeframe',
                     value=(video.start, video.end),
                     max_value=video.end,
                     step=datetime.timedelta(seconds=1),
                     on_change=action_change_timeframe,
                     format=config.SLIDER_TIME_FORMAT)

def display_timepoint_tuner(label: str, tf: 'TimeFrame', tp: 'TimePoint'):
    # TODO: may want to pull the first two lines into a configuration 
    # file or into the user options
    step = datetime.timedelta(milliseconds=100)
    margin = datetime.timedelta(seconds=config.FINE_TUNING_WINDOW)
    d = datetime.datetime(2020, 1, 1, tp.hours, tp.minutes, tp.seconds)
    with st.container(border=False):
        _, col, _ = st.columns([1,30,1])
        return col.slider(
            create_label(label), d - margin, d + margin,
            value=d, format=config.SLIDER_TIME_FORMAT, step=step)

def display_left_boundary(timeframe: 'TimeFrame'):
    date = display_timepoint_tuner('Fine-tune the starting point', timeframe, timeframe.start)
    timepoint = timepoint_from_datetime(date)
    step = 100
    ms = timeframe.start.in_milliseconds()
    frames = get_frames(timeframe.video, ms, step)
    display_sliding_window(st, frames, timepoint)
    st.button("Save starting time", on_click=action_save_starting_time, args=[timepoint])

def display_right_boundary(timeframe: 'TimeFrame'):
    date = display_timepoint_tuner('Fine-tune the ending point', timeframe, timeframe.end)
    timepoint = timepoint_from_datetime(date)
    step = 100
    ms = timeframe.end.in_milliseconds()
    frames = get_frames(timeframe.video, ms, step)
    display_sliding_window(st, frames, timepoint)
    st.button("Save ending time", on_click=action_save_ending_time, args=[timepoint])

def get_frames(video, ms: int, step: int):
    window = get_window(ms, n=config.CONTEXT_SIZE, step=step)
    frames = [Frame(video, ms) for ms in window]
    # TODO. This is to make "Assertion fctx->async_lock" errors less likely, this is
    # much easier to do than the real fix which seems to require dealing with threads.
    time.sleep(1)
    return frames

def get_window(milliseconds: int, n=4, step=100) -> list:
    """Returns a list of timepoints (in milliseconds) in a window around the given
    timepoint in milliseconds."""
    timepoints = []
    for ms in range(n * -step, 0, step):
        timepoints.append(milliseconds + ms)
    timepoints.append(milliseconds)
    for ms in range(0, n * step, step):
        timepoints.append(milliseconds + ms + step)
    return timepoints

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
    #cols = box.columns(len(frames))
    cols = box.columns(cols)
    for i, frame in enumerate(frames):
        display_frame(cols[i], frame)

def display_frame(column, frame, focus=False):
    caption = f'✔︎' if focus else frame.caption()
    column.image(frame.image, channels="BGR", caption=caption)

def process_arguments(args):
    processed_args = {}
    for arg, val in args.items():
        if isinstance(val, dict):
            if val.get('rel') and val.get('loc'):
                processed_args[arg] = f'{val["rel"]}({val["loc"]})'
            elif val['txt']:
                processed_args[arg] = val['txt']
            else:
                processed_args[arg] = None
        elif isinstance(val, str) or val is None:
            processed_args[arg] = val
    return processed_args

def display_inputs(predicate: str, inputs: list):
    # The inputs argument is a list of dictionaries, where each dictionary
    # contains the specification for an argument or property.
    inputs_dict = {}
    if predicate is not None:
        descriptions = [input_signature(d) for d in inputs]
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
                    item = import_session_objects(item)
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
        frames = [Frame(st.session_state.video, o) for o in offsets[:10]]
        display_frames(st, frames, cols=10)
    tiers = sorted(set([a.tier for a in annotations if a.tier]))
    groups = [{"id": tier, "content": tier.lower()} for tier in tiers]
    # Arrived at these numbers experimentally, the height of a tier is 1.3 cm on the 
    # screen and the timeline at the bottom is 1.8 cm. The 42 is a multiplier to get
    # to a number of pixels.
    height = ((len(tiers) * 1.3) + 1.8) * 42
    options = { "selectable": True, "zoomable": True, "stack": False, "height": height }
    timeline_items = get_timeline(annotations)
    try:
        item = streamlit_timeline.st_timeline(timeline_items, groups=groups, options=options)
        if item:
            annotation_pp(item['annotation'])
    except:
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
    objs =  list(sorted(st.session_state.pool.objects[obj_type]['inplay']))
    with st.container(border=True):
        st.text('\n'.join(objs))

def display_predicate_selector(column, key='action_type'):
    label = create_label('Select predicate')
    return st.pills(label, config.PREDICATES.keys(), key=key)

def display_remove_annotation_select():
    return st.selectbox('Remove annotation', [None] + annotation_identifiers())


## Actions
## ----------------------------------------------------------------------------

def action_change_timeframe():
    t1, t2 = st.session_state.opt_timeframe
    if st.session_state.annotation.timeframe is None:
        st.session_state.annotation.timeframe = TimeFrame()
    st.session_state.annotation.timeframe.start = timepoint_from_time(t1)
    st.session_state.annotation.timeframe.end = timepoint_from_time(t2)

def action_add_objects(object_type: str, objects: list):
    """Put the objects in the list in play, that is, move them from the 'available'
    bin to the 'inplay' bin. After this, they will be available as options."""
    st.session_state.pool.put_objects_in_play(object_type, objects)
    with open(st.session_state.io['json'], 'a') as fh:
        for obj in objects:
           fh.write(json.dumps({"add-object": (object_type, obj)}) + '\n')
           message = f'Added {obj} and removed it from the pool'
           st.session_state.messages.append(message)
           log(message)

def action_remove_objects(object_type: str, objects: list):
    """Remove the objects in the list from play, that is, move them from the 'inplay'
    bin to the 'available' bin. After this, they won't be available as options."""
    st.session_state.pool.remove_objects_from_play(object_type, objects)
    with open(st.session_state.io['json'], 'a') as fh:
        for obj in objects:
           fh.write(json.dumps({"remove-object": (object_type, obj)}) + '\n')
           message = f'Removed {obj} and returned it to the pool'
           st.session_state.messages.append(message)
           log(message)

def action_remove_annotation(annotation_id: str):
    if annotation_id is not None:
        with open(st.session_state.io['json'], 'a') as fh:
            fh.write(json.dumps({"remove-annotation": annotation_id}) + '\n')
        remove_annotation(annotation_id)
        message = f"Removed  annotation {annotation_id}"
        st.session_state.messages.append(message)
        log(message)

def action_save_starting_time(timepoint: 'TimePoint'):
    st.session_state.annotation.timeframe.start = timepoint
    st.session_state.opt_tune_start = False
    log(f'Saved starting time {timepoint}')

def action_save_ending_time(timepoint: 'TimePoint'):
    st.session_state.annotation.timeframe.end = timepoint
    st.session_state.opt_tune_end = False
    log(f'Saved ending time {timepoint}')

def add_object(object_type: str, obj: str):
    st.session_state.pool.add_object(object_type, obj)

def remove_annotation(annotation_id: str):
    st.session_state.annotations = \
        [a for a in st.session_state.annotations if a.identifier != annotation_id]


## Various other utilities
## ----------------------------------------------------------------------------

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

def get_video_location_from_command_line() -> str:
    return sys.argv[1] if len(sys.argv) > 1 else None

def load_annotations():
    filename = st.session_state.io['json']
    if not os.path.isfile(filename):
        pathlib.Path(filename).touch()
    video_path = st.session_state.video.path
    with open(filename) as fh:
        raw_annotations = [json.loads(line) for line in fh]
        annotations = []
        removed_annotations = []
        for raw_annotation in raw_annotations:
            if 'add-object' in raw_annotation:
                obj_type, obj = raw_annotation['add-object'][:2]
                st.session_state.pool.put_object_in_play(obj_type, obj)
            elif 'remove-object' in raw_annotation:
                obj_type, obj = raw_annotation['remove-object'][:2]
                st.session_state.pool.remove_object_from_play(obj_type, obj)
            elif 'remove-annotation' in raw_annotation:
                removed_annotations.append(raw_annotation['remove-annotation'])
            else:
                annotation = Annotation().import_fields(raw_annotation)
                annotations.append(annotation)
        annotations = [a for a in annotations if not a.identifier in removed_annotations]
        st.session_state.annotations = annotations
        log(f'Loaded annotations from {filename}')

def annotation_identifiers():
    return [annotation.identifier for annotation in st.session_state.annotations]

def create_timeframe_from_slider_inputs(t1, t2):
    # after initial selection we do not have milliseconds yet
    return TimeFrame(TimePoint(hours=t1.hour, minutes=t1.minute, seconds=t1.second),
                     TimePoint(hours=t2.hour, minutes=t2.minute, seconds=t2.second),
                     video=st.session_state.video)

def updated_timepoint(timepoint: 'TimePoint', milliseconds: int):
    """Takes a TimePoint and returns a new one which is the same except that the
    specified amount of millicesonds is added."""
    total = timepoint.in_milliseconds() + int(milliseconds)
    return TimePoint(milliseconds=total)

def timepoint_from_datetime(datetime: datetime.datetime):
    t = datetime.time()
    ms = t.microsecond // 1000
    return TimePoint(
        hours=t.hour, minutes=t.minute, seconds=t.second, milliseconds=ms)

def timepoint_from_time(t: datetime.time):
    ms = t.microsecond // 1000
    return TimePoint(
        hours=t.hour, minutes=t.minute, seconds=t.second, milliseconds=ms)

def timestamp():
    return datetime.datetime.now().strftime('%Y%m%d:%H%M%S')

def log(text):
    with open(st.session_state.io['log'], 'a') as fh:
        fh.write(f'{timestamp()}\t{text}\n')

def create_label(text: str, size='normalsize'):
    """Return formatted text that can be used as a label of a particular size,
    for sizes use the ones defined by LaTeX (small, large, Large, etcetera)."""
    return r"$\textsf{" + f'\\{size} {text}' + "}$"

def current_timeframes(task: str) -> list:
    """Returns all <name, timeframe> pairs of the current annotations in the task."""
    annos = st.session_state.annotations
    return [(anno.name, anno.timeframe) for anno in annos if anno.task == task]

def overlap(tf1: 'TimeFrame', tf2: 'TimeFrame'):
    """Return True if two time frames overlap, False otherwise."""
    # TODO: mayhap put this on the TimeFrame class
    if tf1.end <= tf2.start:
        return False
    if tf2.end <= tf1.start:
        return False
    return True

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


class ObjectPool:

    def __init__(self):
        self.objects = {}
        self.object_types = []

    def __getattr__(self, attr):
        if attr in self.object_types:
            return self.objects[attr]
        else:
            raise AttributeError(
                f"type object '{self.__class__.__name__}' has no attribute '{attr}'")

    def __str__(self):
        def get_count(obj_type: str):
            return sum(len(v) for v in self.objects[obj_type].values())
        counts = [f"{ot}={get_count(ot)}" for ot in self.object_types]
        return f'<ObjectPool {" ".join(counts)}>'

    def get_available(self, obj_type: str):
        return self.objects[obj_type]['available']

    def get_in_play(self, obj_type: str):
        return self.objects[obj_type]['inplay']

    def add_object_type(self, obj_type: str):
        self.objects[obj_type] = {'available': set(), 'inplay': set()}
        self.object_types.append(obj_type)

    def add_object(self, obj_type: str, obj: str):
        if obj_type not in self.objects:
            self.add_object_type(obj_type)
        self.objects[obj_type]['available'].add(obj)

    def add_objects(self, obj_type: str, objs: list):
        if obj_type not in self.objects:
            self.add_object_type(obj_type)
        self.objects[obj_type]['available'].update(objs)

    def put_objects_in_play(self, obj_type: str, objs: list):
        for obj in objs:
            self.put_object_in_play(obj_type, obj)

    def put_object_in_play(self, obj_type: str, obj: str):
        if obj_type in self.objects:
            try:
                self.objects[obj_type]['available'].remove(obj)
            except KeyError:
                # TODO: this happens when reloading the annotations
                # should perhaps reset the pools when reloading
                log(f'{obj} was already put in play')
            self.objects[obj_type]['inplay'].add(obj)

    def remove_objects_from_play(self, obj_type: str, objs: list):
        for obj in objs:
            self.remove_object_from_play(obj_type, obj)

    def remove_object_from_play(self, obj_type: str, obj: str):
        if obj_type in self.objects:
            try:
                self.objects[obj_type]['inplay'].remove(obj)
            except KeyError:
                # TODO: this happens when reloading the annotations
                # should perhaps reset the pools when reloading
                log(f'{obj} was already removed from play')
            self.objects[obj_type]['available'].add(obj)

    def as_json(self):
        pool = {}
        for obj_type, data in self.objects.items():
            pool[obj_type] = data
        return pool


@functools.total_ordering
class TimePoint:

    """Utility class to deal with time points, where a time point refers to an offset
    in the video. It is flexible in that it allows any number of seconds, minutes and
    hours upon initialization, as long as the values are all integers >= 0. It will
    normalize itself to cap seconds and minutes at 59 though."""

    def __init__(self, hours=0, minutes=0, seconds=0, milliseconds=0):
        #if hours < 0 or minutes < 0 or seconds < 0 or milliseconds < 0:
        #    raise ValueError('Values need to be >= 0')
        #print('===', hours, minutes, seconds, milliseconds)
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.milliseconds = milliseconds
        self.normalize()

    def __str__(self):
        return f'<{self.__class__.__name__} {self.timestamp()}>'

    def __eq__(self, other):
        return self.in_milliseconds() == other.in_milliseconds()

    def __lt__(self, other):
        return self.in_milliseconds() < other.in_milliseconds()

    def copy(self):
        return TimePoint(
            hours=self.hours, minutes=self.minutes,
            seconds=self.seconds, milliseconds=self.milliseconds)

    def hh(self):
        """Return number of hours as a string."""
        return f'{self.hours:02d}'

    def mm(self):
        """Return number of minutes as a string."""
        return f'{self.minutes:02d}'

    def ss(self):
        """Return number of seconds as a string."""
        return f'{self.seconds:02d}'

    def mmm(self):
        return f'{self.milliseconds:03d}'

    def timestamp(self, short=False):
        if short:
            return f'{self.mm()}:{self.ss()}.{self.mmm()}'
        else:
            return f'{self.hh()}:{self.mm()}:{self.ss()}.{self.mmm()}'

    def normalize(self):
        """Normalize values so that millisseconds < 1000, and seconds and minutes
        are < 60. Normalization leaves the hours alone"""
        #print('>>>',self)
        #print('---', type(self.seconds), type(self.milliseconds))
        #print('---', self.seconds, self.milliseconds)
        if self.milliseconds > 999:
            seconds = int(self.milliseconds / 1000)
            self.seconds += seconds
            self.milliseconds = self.milliseconds - (seconds * 1000)
        if self.seconds > 59:
            minutes = int(self.seconds / 60)
            self.minutes += minutes
            self.seconds = self.seconds - (minutes * 60)
        if self.minutes > 59:
            hours = int(self.minutes / 60)
            self.hours += hours
            self.minutes = self.minutes - (hours * 60)

    def in_seconds(self):
        return self.hours * 3600 + self.minutes * 60 + self.seconds

    def in_milliseconds(self):
        return self.in_seconds() * 1000 + self.milliseconds

    def adjust_seconds(self, seconds: int):
        """Add seconds to the timepoint and normalize."""
        # TODO: must also know how to deal with values going negative
        self.seconds += seconds
        self.normalize()

    def adjust_milliseconds(self, milliseconds: int):
        """Add seconds to the timepoint and normalize."""
        # TODO: must also know how to deal with values going negative
        self.milliseconds += milliseconds
        self.normalize()


class TimeFrame:

    def __init__(self, start: TimePoint = None, end: TimePoint = None, video=None):
        self.start = start
        self.end = end
        self.video = video

    def __str__(self):
        return f'{self.start} ==> {self.end}  [length={len(self)}]'

    def __len__(self):
        if self.start is not None and self.end is not None:
            return self.end.in_seconds() - self.start.in_seconds()
        else:
            return 0

    def copy(self):
        return TimeFrame(
            start=self.start.copy(), end=self.end.copy(), video=self.video)

    def adjust_start(self, milliseconds: int):
        """Adjust the start point, using milliseconds."""
        self.start.adjust_milliseconds(milliseconds)

    def adjust_end(self, milliseconds: int):
        """Adjust the end point, using milliseconds."""
        self.end.adjust_milliseconds(milliseconds)

    def frame_at(self, milliseconds: int):
        return Frame(self.video, milliseconds)

    def slice_to_left(self, milliseconds: int, n=4, step=100):
        frames = []
        for ms in range(n * -step, 0, step):
            frames.append(Frame(self.video, milliseconds + ms))
        return frames

    def slice_to_right(self, milliseconds: int, n=4, step=100):
        frames = []
        for ms in range(0, n * step, step):
            frames.append(Frame(self.video, milliseconds + ms))
        return frames
        

class Video:

    """Class to wrap a cv2.VideoCapture instance and add some goodies to it."""

    def __init__(self, video_path: str):
        self.path = video_path
        self.filename = os.path.basename(video_path)
        self.vidcap = cv2.VideoCapture(video_path)
        self.start = datetime.time.min
        self.end = self.get_video_end()
        self._length = self.end.hour * 3600 + self.end.minute * 60 + self.end.second

    def __str__(self):
        return f'<Video path={os.path.basename(self.path)} {len(self)}>'

    def __len__(self):
        return self._length

    def get_video_end(self) -> datetime.time:
        """Return the length of the video as a datetime.time object (which means that
        videos cannotbe longer than 24 hours)."""
        fps = self.vidcap.get(cv2.CAP_PROP_FPS)
        frame_count = int(self.vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        seconds = frame_count / fps
        minutes = int(seconds / 60)
        hours = int(minutes / 60)
        seconds = int(seconds % 60)
        minutes = int(minutes % 60)
        return datetime.time(hour=hours, minute=minutes, second=seconds-1)

    def extract_frame(self, offset: int):
        """Extract a frame from the video at a particular offset in milliseconds,
        return the image or None if extraction failed."""
        self.vidcap.set(cv2.CAP_PROP_POS_MSEC, offset)
        success, image = self.vidcap.read()
        return image if success else None

    def extract_frame_at_second(self, offset: int):
        return self.extract_frame(offset * 1000)

    def extract_frame_at_millisecond(self, offset: int):
        return self.extract_frame(offset)

    def extract_frame_at_timepoint(self, timepoint: TimePoint):
        return self.extract_frame(timepoint.in_milliseconds())


class Frame:

    """Class to wrap the frame extracted with vidcap.read()."""

    def __init__(self, vidcap, offset: int):
        self.timepoint = TimePoint(milliseconds=offset)
        if offset in st.session_state.cache:
            image = st.session_state.cache[offset]
        else:
            image = vidcap.extract_frame(offset)
            image = st.session_state.cache[offset] = image
        self.image = image
        self.success = False if self.image is None else True 

    def __str__(self):
        timestamp = self.timepoint.timestamp()
        return f'<{self.__class__.__name__} t={timestamp} image={self.success}>'

    def caption(self, short=True):
        return self.timepoint.timestamp(short=short)


@functools.total_ordering
class Annotation:

    """Instances of this class contain all information relevant to a particular
    annotation. Annotations have four kinds of information:

    - start and end offsets (because they are interval annotations)
    - a predicate (could be None, but usually something like Put or Remove)
    - a dictionary with arguments for the predicate
    - a dictionary with any other properties

    """

    def __init__(self, task: str = None, tier: str = None,
                 identifier: str = None, video_path: str = None,
                 timeframe: TimeFrame = None, properties: dict = {},
                 predicate: str = None, arguments: dict = {}):
        self.identifier = identifier
        self.task = config.TASK if task is None else task
        self.tier = tier
        self.video_path = video_path
        self.timeframe = TimeFrame() if timeframe is None else timeframe
        self.predicate = predicate
        self.arguments = arguments
        self.properties = properties
        self.errors = []
        self.missing_fields = []

    def __str__(self):
        return (
            f'{self.task} {self.tier} {self.identifier} {self.name} {self.tier}'
            + f' {self.start} {self.end} {self.as_formula()} {self.properties}')

    def __eq__(self, other):
        return self.start == other.start

    def __lt__(self, other):
        return self.start < other.start

    def assign_identifier(self):
        max_identifier = 0
        for annotation in st.session_state.annotations:
            max_identifier = max(max_identifier, int(annotation.identifier[1:]))
        self.identifier = f'a{max_identifier+1:04d}'

    def import_fields(self, annotation: dict):
        self.identifier = annotation['identifier']
        self.task = annotation.get('task')
        self.tier = annotation.get('tier')
        self.properties = annotation['properties']
        self.predicate = annotation['predicate']
        self.arguments = annotation['arguments']
        tp1 = TimePoint(milliseconds=annotation['start'])
        tp2 = TimePoint(milliseconds=annotation['end'])
        self.timeframe = TimeFrame(start=tp1, end=tp2)
        return self

    @classmethod
    def columns(cls):
        return ['task', 'tier', 'id', 'name', 'start', 'end', 'predicate', 'properties']

    @property
    def name(self):
        return self.elan_identifier()

    @property
    def start(self):
        if self.timeframe is None or self.timeframe.start is None:
            return None
        return self.timeframe.start.in_milliseconds()

    @property
    def end(self):
        if self.timeframe is None or self.timeframe.end is None:
            return None
        return self.timeframe.end.in_milliseconds()
    
    def matches(self, term: str):
        """Returns True if the search term occurs in the identifier, name or formula."""
        if not term:
            return True
        term = term.lower()
        if term in str(self.task).lower() + str(self.tier).lower():
            return True
        if term in self.name.lower() + self.identifier.lower():
            return True
        if term in self.as_formula().lower():
            return True
        if term in str(self.properties).lower():
            return True
        return False

    def is_valid(self):
        """Checker whether the annotation is not missing any required fields."""
        self.errors = []
        self.check_task_and_tier()
        self.check_start_and_end()
        self.check_predicate_and_arguments()
        self.check_properties()
        return True if not self.errors else False

    def check_task_and_tier(self):
        if self.task is None:
            self.errors.append(f'WARNING: the task is not specified')
        if self.tier is None:
            self.errors.append(f'WARNING: the tier is not specified')

    def check_start_and_end(self):
        """Check the start and end values of the annotation, add the the erros list
        if any errors were found."""
        # TODO: add check for out of bounds start or end
        if self.start is None:
            self.errors.append(f'WARNING: the start position is not specified')
        if self.end is None:
            self.errors.append(f'WARNING: the end position is not specified')
        if self.start is not None and self.end is not None:
            if self.start > self.end:
                self.errors.append(
                    'WARNING: the start of the interval cannot be before the end')

    def check_predicate_and_arguments(self):
        """ Check the predicate and its arguments, add the the erros list
        if any errors were found."""
        if self.predicate is None:
            self.errors.append(f'WARNING: the predicate is not specified')
        if self.predicate:
            argument_specifications = config.PREDICATES.get(self.predicate, {})
            arguments_idx = { a['type']: a for a in argument_specifications }
            for arg_name, arg_value in self.arguments.items():
                optional = arguments_idx[arg_name].get('optional', False)
                if not arg_value and not optional:
                    self.errors.append(
                        f'WARNING: required argument "{arg_name}" is not specified')

    def check_properties(self):
        """Check the properties dictionary of the annotation, add the the erros list
        if any errors were found."""
        properties_idx = { p['type']: p for p in config.PROPERTIES }
        for prop, value in self.properties.items():
            # There is something iffy here with the tier property which can be in
            # the properties, but does not need to be in the defined properties 
            if prop not in properties_idx:
                continue
            optional = properties_idx[prop].get('optional', False)
            if not value and not optional:
                self.errors.append(f'WARNING: property "{prop}"" is not specified')
   
    def elan_identifier(self):
        """Cobble together an Elan "identifier" from the identifier and the start
        time. The elan identifier is more like a summary, using a prefix plus the
        minutes and seconds from the start timepoint, it is not required to be
        unique."""
        try:
            # TODO: this may be different for some tasks if we don't use 
            # 'predicate' for that field
            prefix = 'X' if self.predicate is None else self.predicate[0]
            tp = TimePoint(milliseconds=self.start)
            offset= f'{tp.mm()}{tp.ss()}'
            return f'{prefix}{offset}'
        except:
            return None

    def as_formula(self):
        formatted_args = ', '.join([f'{a}="{v}"' for a,v in self.arguments.items()])
        return f'{str(self.predicate)}({formatted_args})'

    def as_json(self):
        return {
            'task': self.task,
            'tier': self.tier,
            'identifier': self.identifier,
            'name': self.name,
            'start': self.start,
            'end': self.end,
            'predicate': self.predicate,
            'arguments': self.arguments,
            'properties': self.properties }

    def as_elan(self):
        start = f'{self.start/1000:.3f}' if self.start else 'None'
        end = f'{self.end/1000:.3f}' if self.end else 'None'
        offsets = f'{start}\t{end}'
        return f'{self.tier}\t{offsets}\t{self.elan_identifier()}: {self.as_formula()}'

    def as_row(self):
        return [self.task, self.tier, self.identifier, self.name,
                self.start_as_string(), self.end_as_string(),
                self.as_formula(), str(self.properties)]

    def start_as_string(self):
        return self.point_as_string(self.start)

    def end_as_string(self):
        return self.point_as_string(self.end)

    def point_as_string(self, ms: int):
        # TODO: this should not be an instance method here
        if ms is None:
            return 'None'
        t = TimePoint(milliseconds=ms)
        return f'{t.mm()}:{t.ss()}.{t.mmm()}'

    def calculate_tier(self, tf: TimeFrame, selected_tier: str):
        """Calculate the tier for an annotation. There are three cases:
        1. Tasks with only one tier where the tier is defined in the configuration
        2. Tasks where the tier is user-defined (like the DPIP gesture annotation)
        3. Task that assume two tiers where the second is used for annotations that
           overlap with an annotation in the first tier (like the DPIP action
           annotation task).
        """
        # Case 1: tier comes from the configuration
        if not config.MULTIPLE_TIERS:
            self.tier = config.TIER
        # Case 2: tier comes from the second argument
        elif config.TIER_IS_DEFINED_BY_USER:
            self.tier = selected_tier
        # Case 3: calculate the tier
        else:
            #print('---', tf)
            taken = current_timeframes(self.task)
            for name, taken_tf in taken:
                #print('   ', taken_tf, overlap(tf, taken_tf))
                if overlap(tf, taken_tf):
                    #print('... overlap found with', name, taken_tf)
                    self.tier = config.TIERS[1]
                    return
            #print('... no overlap found')
            self.tier = config.TIERS[0]

    def copy(self):
        return Annotation(
            task=self.task,
            tier=self.tier,
            identifier=self.identifier,
            timeframe=self.timeframe.copy(),
            predicate=self.predicate,
            arguments=deepcopy(self.arguments),
            properties=deepcopy(self.properties))

    def save(self):
        if self.is_valid():
            self.assign_identifier()
            st.session_state.annotations.append(self.copy())
            json_file = st.session_state.io['json']
            elan_file = st.session_state.io['elan']
            with open(json_file, 'a') as fh:
                fh.write(json.dumps(self.as_json()) + '\n')
            with open(elan_file, 'a') as fh:
                fh.write(self.as_elan() + '\n')
            st.session_state.action_type = None
            log(f'Saved annotation {self.identifier} {self.as_formula()}')
        st.session_state.errors = self.errors
        st.session_state.opt_show_boundary = False
        st.session_state.annotation = Annotation()
        for error in self.errors:
            log(error)
