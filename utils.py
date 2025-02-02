"""

Utilities for the DPIP annotators

"""


import os
import sys
import json
import time
import pathlib
import datetime
import pathlib
from copy import deepcopy

import cv2
import pandas as pd
import streamlit as st

import config


## Streamlit utilities
## ----------------------------------------------------------------------------

def intialize_session_state():
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
    if not 'objects' in st.session_state:
        st.session_state.objects = {
            'pool': create_object_pool(),
            'inplay': set() }
    if not 'annotations' in st.session_state:
        load_annotations()
    if not 'windows' in st.session_state:
        st.session_state.windows = WindowCache()
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
        f'Blocks: {len(st.session_state.objects["inplay"])}\n'
        + f'Annotations: {len(st.session_state.annotations)}')
    st.sidebar.code(text, language='yaml')

def sidebar_display_tool_mode():
    st.sidebar.header('Tool mode', divider=True)
    return st.sidebar.radio(
        "Tool mode",
        ['add annotations', 'show annotations', 'show blocks', 'help', 'dev'],
        key='opt_mode',
        label_visibility='collapsed')

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

def sidebar_display_dev_controls():
    st.sidebar.header('Developer goodies', divider=True)
    dev_session = st.sidebar.checkbox('Show session_state', value=False)
    dev_log = st.sidebar.checkbox('Show log', value=False)
    return {
        'session_state': dev_session,
        'log': dev_log,
        }

def display_video(video: 'Video', width, seconds):
    st.info(video.filename)
    margin = max((100 - width), 0.01)
    container, _ = st.columns([width, margin])
    container.video(video.path, start_time=seconds)

def display_timeframe_slider():
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
    if False:
        # for now we are not showing those other timeframes
        left_context = tf.slice_to_left(tp.in_milliseconds(), n=4, step=1000)
        first_frames = tf.slice_to_right(tp.in_milliseconds(), n=5, step=1000)
        header = 'Window of nine frames around the selected start point or end point'
        display_frames(st, left_context + first_frames, header=header)
    box = st.container(border=True)
    return box.slider(
        create_label(label), d - margin, d + margin,
        value=d, format=config.SLIDER_TIME_FORMAT, step=step)

def display_left_boundary(timeframe: 'TimeFrame'):
    date = display_timepoint_tuner('Fine-tune the starting point', timeframe, timeframe.start)
    timepoint = timepoint_from_datetime(date)
    step = 100
    ms = timeframe.start.in_milliseconds()
    add_frames_to_cache(timeframe, ms, step)
    display_sliding_window(st, st.session_state.windows[ms], timepoint)
    st.button("Save starting time", on_click=action_save_starting_time, args=[timepoint])

def display_right_boundary(timeframe: 'TimeFrame'):
    date = display_timepoint_tuner('Fine-tune the ending point', timeframe, timeframe.end)
    timepoint = timepoint_from_datetime(date)
    step = 100
    ms = timeframe.end.in_milliseconds()
    add_frames_to_cache(timeframe, ms, step)
    display_sliding_window(st, st.session_state.windows[ms], timepoint)
    st.button("Save ending time", on_click=action_save_ending_time, args=[timepoint])

def add_frames_to_cache(timeframe, ms, step):
    """Makes sure that the frames needed are in the cache."""
    if ms not in st.session_state.windows.data:
        window = timeframe.get_window(ms, n=config.CONTEXT_SIZE, step=step)
        log(f'Cached frame window at {ms}')
        st.session_state.windows[ms] = window
        # TODO. This is to make "Assertion fctx->async_lock" errors less likely,
        # this is much easier to do than the real fix which seems to require 
        # dealing with threads.
        time.sleep(1)

def display_sliding_window(column, frames, tp, header=None):
    """Display frames horizontally in a box."""
    box = column.container(border=True)
    if header is not None:
        box.write(header)
    cols = box.columns(len(frames))
    for i, frame in enumerate(frames):
        is_focus = False
        if tp.in_milliseconds() == frame.timepoint.in_milliseconds():
            is_focus = True
        display_frame(cols[i], frame, focus=is_focus)

def display_frames(column, frames, header=None):
    """Display frames horizontally in a box."""
    box = column.container(border=True)
    if header is not None:
        box.write(header)
    cols = box.columns(len(frames))
    for i, frame in enumerate(frames):
        display_frame(cols[i], frame)

def display_frame(column, frame, focus=False):
    caption = f'✔︎' if focus else frame.caption()
    column.image(frame.image, channels="BGR", caption=caption)
    
def display_arguments(arguments: list):
    arg_dict = {}
    if arguments:
        cols = st.columns(len(arguments))
        args = [''] * len(arguments)
        for i, arg in enumerate(arguments):
            with cols[i]:
                if arg == 'Object':
                    blocks = list(sorted(st.session_state.objects['inplay']))
                    args[i] = st.selectbox(arg, [None] + blocks)
                else:
                    args[i] = st.text_input(arg)
                arg_dict[arg] = args[i]
    return arg_dict

def display_annotation(annotation, show_options: dict):
    st.info('Current annotation')
    df = pd.DataFrame([annotation.as_row()], columns=annotation.columns())
    st.table(df)
    if show_options['elan']:
        st.code(annotation.as_elan())
    if show_options['json']:
        with st.container(border=True):
            st.json(annotation.as_json())

def display_annotations():
    with st.container(border=True):
        st.text('All annotations, using order of creation from last to first')
        term = st.text_input('Search annotations')
        rows = []
        for annotation in reversed(st.session_state.annotations):
            if not term or term in annotation.as_formula():
                rows.append(annotation.as_row())
        df = pd.DataFrame(rows, columns=ActionAnnotation.columns())
        st.table(df)

def display_errors():
    for error in st.session_state.errors:
        st.error(error)
    st.session_state.errors = []

def display_messages():
    for message in st.session_state.messages:
        st.info(message)
    st.session_state.messages = []

def display_available_blocks():
    st.info('**Currently available blocks**')
    blocks = list(sorted(st.session_state.objects['inplay']))
    with st.container(border=True):
        st.text('\n'.join(blocks))

def display_action_type_selector(column, key='action_type'):
    label = create_label('Select action type')
    return st.pills(label, config.ACTION_TYPES, key=key)

def display_add_block_select(column):
    """Displays a selectbox for selecting a block from the pool and returns what
    the selectbox returns."""
    return column.selectbox(
        'Add object from pool',
        [None] + sorted(st.session_state.objects['pool']),
        label_visibility='collapsed')

def display_remove_block_select(column):
    """Displays a selectbox for removing a block from the pool and returns what
    the selectbox returns."""
    return column.selectbox(
        'Remove object and return to pool',
        [None] + sorted(st.session_state.objects['inplay']),
        label_visibility='collapsed')

def display_remove_annotation_select():
    return st.selectbox('Remove annotation', [None] + annotation_identifiers())


## Actions
## ----------------------------------------------------------------------------

def action_change_timeframe():
    t1, t2 = st.session_state.opt_timeframe
    st.write(st.session_state.annotation.timeframe)
    if st.session_state.annotation.timeframe is None:
        st.session_state.annotation.timeframe = TimeFrame()
    st.session_state.annotation.timeframe.start = timepoint_from_time(t1)
    st.session_state.annotation.timeframe.end = timepoint_from_time(t2)

def action_add_block(block: str):
    add_block(block)
    with open(st.session_state.io['json'], 'a') as fh:
        fh.write(json.dumps({"add-block": block}) + '\n')
    message = f'Added {block} and removed it from the pool'
    st.session_state.messages.append(message)
    log(message)

def action_remove_block(block: str):
    remove_block(block)
    with open(st.session_state.io['json'], 'a') as fh:
        fh.write(json.dumps({"remove-block": block}) + '\n')
    message = f'Removed {block} and added it back to the pool'
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

def add_block(block):
    st.session_state.objects['inplay'].add(block)
    try:
        st.session_state.objects['pool'].remove(block)
    except KeyError:
        pass

def remove_block(block):
    st.session_state.objects['pool'].add(block)
    try:
        st.session_state.objects['inplay'].remove(block)
    except KeyError:
        pass

def remove_annotation(annotation_id: str):
    st.session_state.annotations = \
        [a for a in st.session_state.annotations if a.identifier != annotation_id]


## Various other utilities
## ----------------------------------------------------------------------------

def get_video_location_from_command_line():
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
            if 'add-block' in raw_annotation:
                add_block(raw_annotation['add-block'])
            elif 'remove-block' in raw_annotation:
                remove_block(raw_annotation['remove-block'])
            elif 'remove-annotation' in raw_annotation:
                removed_annotations.append(raw_annotation['remove-annotation'])
            else:
                timeframe = TimeFrame(
                    start=TimePoint(milliseconds=raw_annotation['start']),
                    end=TimePoint(milliseconds=raw_annotation['end']))
                annotation = ActionAnnotation(
                    identifier=raw_annotation['identifier'],
                    video_path=video_path,
                    timeframe=timeframe,
                    predicate=raw_annotation['action'],
                    arguments=raw_annotation['arguments'] )
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

def create_object_pool():
    pool = []
    for size in ('Large', 'Small'):
        for color in ('Green', 'Red', 'Blue', 'Yellow'):
            for identifier in range(1, 7):
                pool.append(f'{size}{color}Block{identifier}')
    return set(pool)


class WindowCache:

    def __init__(self):
        self.data = {}

    def __len__(self):
        return len(self.data)

    def __str__(self):
        points = '{' + ' '.join([str(ms) for ms in self.data.keys()]) + '}'
        return f'<WindowCache with {len(self)} timepoints  {points}>'

    def __getitem__(self, i):
        return self.data[i]

    def __setitem__(self, i, val):
        self.data[i] = val


class TimePoint:

    """Utility class to deal with time points, where a time point refers to an offset
    in the video. It is flexible in that it allows any number of seconds, minutes and
    hours upon initialization, as long as the values are all integers >= 0. It will
    normalize itself to cap seconds and minutes at 59 though."""

    def __init__(self, hours=0, minutes=0, seconds=0, milliseconds=0):
        #if hours < 0 or minutes < 0 or seconds < 0 or milliseconds < 0:
        #    raise ValueError('Values need to be >= 0')
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.milliseconds = milliseconds
        self.normalize()

    def __str__(self):
        return f'<{self.__class__.__name__} {self.timestamp()}>'

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

    def first_frames(self, n=4, step=100):
        """Return the first n frames (timepoints) in the timeframe, with the specified
        spacing between each frame."""
        return self.slice_to_right(self.start.in_milliseconds(), n=n, step=step)

    def last_frames(self, n=4, step=100):
        """Return the last n frames (timepoints) in the timeframe, with the specified
        spacing between each frame."""
        return self.slice_to_left(self.end.in_milliseconds(), n=n, step=step)

    def left_context(self, n=4, step=100):
        return self.slice_to_left(self.start.in_milliseconds(), n=n, step=step)

    def right_context(self, n=4, step=100):
        return self.slice_to_right(self.end.in_milliseconds(), n=n, step=step)

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

    def get_window(self, milliseconds: int, n=4, step=100):
        frames = []
        for ms in range(n * -step, 0, step):
            frames.append(Frame(self.video, milliseconds + ms))
        frames.append(Frame(self.video, milliseconds))
        for ms in range(0, n * step, step):
            frames.append(Frame(self.video, milliseconds + ms + step))
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
        self.image = vidcap.extract_frame(offset)
        self.success = False if self.image is None else True 

    def __str__(self):
        timestamp = self.timepoint.timestamp()
        return f'<{self.__class__.__name__} t={timestamp} image={self.success}>'

    def caption(self, short=True):
        return self.timepoint.timestamp(short=short)


class Annotation:

    """Annotations have types (action or gesture) and predicates (for example, for
    actions we have put and remove). In addition, annotations are intervals so they
    have start and end offsets."""

    def __init__(self, identifier : str = None, video_path: str = None,
                 timeframe: TimeFrame = None, participant: str = None,
                 predicate: str = None, arguments: dict = {}):
        self.identifier = identifier
        self.video_path = video_path
        self.timeframe = TimeFrame() if timeframe is None else timeframe
        self.participant = participant
        self.predicate = predicate
        self.arguments = arguments
        self.errors = []

    def __str__(self):
        return (
            f'{self.identifier} {self.start} {self.end},' +
            f' {self.participant} {self.as_formula()})')

    @classmethod
    def columns(cls):
        return []

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
    
    def is_valid(self):
        """Checker whether the annotation is not missing any required fields."""
        self.errors = []
        # TODO: add check for out of bounds start or end
        if self.start is None:
            self.errors.append(f'WARNING: start position is not specified')
        if self.end is None:
            self.errors.append(f'WARNING: end position is not specified')
        if self.predicate is None:
            self.errors.append(f'WARNING: {self.annotation_type()} type is not specified')
        for arg_name, arg_value in self.arguments.items():
            if not arg_value:
                self.errors.append(
                    f'WARNING: required argument "{arg_name}" is not specified')
        if self.start is not None and self.end is not None:
            if self.start > self.end:
                self.errors.append(
                    'WARNING: the start of the interval cannot be before the end')
        return True if not self.errors else False

    def elan_identifier(self):
        """Cobble together an Elan "identifier" from the identifier and the start
        time. The elan identifier is more like a summary, using a prefix plus the
        minutes and seconds from the start timepoint, it is not required to be
        unique."""
        # allow for the case where the action/gesture type is not generated yet
        prefix = 'X' if self.predicate is None else self.predicate[0]
        tp = TimePoint(seconds=self.start)
        offset= f'{tp.mm()}{tp.ss()}'
        return f'{prefix}{offset}'

    def as_formula(self):
        formatted_args = ', '.join([f'{a}="{v}"' for a,v in self.arguments.items()])
        return f'{str(self.predicate)}({formatted_args})'

    def as_json(self):
        return {
            'identifier': self.identifier,
            'start': self.start,
            'end': self.end,
            'participant': self.participant,
            'action': self.predicate,
            'arguments': self.arguments
        }

    def as_elan(self):
        offsets = f'{self.start/1000:.3f}\t{self.end/1000:.3f}.0'
        return f'ACTION\t{offsets}\t{self.elan_identifier()}: {self.as_formula()}'

    def as_row(self):
        return [self.identifier, self.start_as_string(), self.end_as_string(),
                self.participant, self.predicate, self.as_formula()]

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

    def copy(self):
        return Annotation(
            identifier=self.identifier,
            video_path=self.video_path,
            participant=self.participant,
            predicate=self.predicate,
            timeframe=self.timeframe.copy(),
            arguments=deepcopy(self.arguments))

    def save(self):
        if self.is_valid():
            self.assign_identifier()
            #print(self)
            st.session_state.annotations.append(self.copy())
            json_file = st.session_state.io['json']
            elan_file = st.session_state.io['elan']
            with open(json_file, 'a') as fh:
                fh.write(json.dumps(self.as_json()) + '\n')
            with open(elan_file, 'a') as fh:
                fh.write(self.as_elan())
            st.session_state.action_type = None
            log(f'Saved annotation {self.identifier} {self.as_formula()}')
        st.session_state.errors = self.errors
        st.session_state.opt_show_boundary = False
        st.session_state.annotation = ActionAnnotation()
        for error in self.errors:
            log(error)


class GestureAnnotation(Annotation):

    identifier = 0

    def __init__(self, video_path: str, start: int, end: int,
                 participant: str, subtype: str, arguments: list):
        self.identifier = self.get_identifier()
        super().__init__(
            video_path=video_path, start=start, end=end,
            participant=participant, subtype=subtype, arguments=arguments)

    @staticmethod
    def annotation_type():
        return 'Gesture'

    def get_identifier(self):
        self.__class__.identifier += 1
        return f'g{self.__class__.identifier:04d}'


class ActionAnnotation(Annotation):

    # TODO: we now get gaps when we fail to add an annotation, maybe assign
    # identifier when we add the annotation (after testing for validity), or
    # else go back to using an identifier created from a timestamp.

    identifier = 1

    def __init__(self, identifier: str = None, video_path: str = None,
                 timeframe: TimeFrame = None, predicate: str = None,
                 arguments: list = []):
        super().__init__(
            identifier=identifier, video_path=video_path, timeframe=timeframe,
            participant='Builder', predicate=predicate, arguments=arguments)

    @classmethod
    def columns(cls):
        return ['id', 'start', 'end', 'participant', 'predicate', 'formula']

    @staticmethod
    def annotation_type():
        return 'Action'

    def assign_identifier(self):
        max_identifier = 0
        for annotation in st.session_state.annotations:
            max_identifier = max(max_identifier, int(annotation.identifier[1:]))
            print(annotation.identifier)
        self.identifier = f'a{max_identifier+1:04d}'


