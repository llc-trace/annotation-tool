"""

TODO: somewhat random behavior when selecting offset out of bounds
    either error or not updating images

"""


import os
import sys
import json
import datetime

import cv2
import pandas as pd
import streamlit as st

import config


## Streamlit utilities

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
    if not 'errors' in st.session_state:
        st.session_state.errors = []
    if not 'messages' in st.session_state:
        st.session_state.messages = []

def display_sidebar_seek_inputs():
    st.sidebar.markdown("### Seek offset in video (hh:mm:ss)")
    col1, spacer1, col2, spacer2, col3, _ = st.sidebar.columns([4,1,4,1,4,6])
    hours = col1.number_input(
        'hh', min_value=0, label_visibility="collapsed")
    minutes = col2.number_input(
        'mm', min_value=0, label_visibility="collapsed")
    seconds = col3.number_input(
        'ss', min_value=0, label_visibility="collapsed")
    spacer1.write(':')
    spacer2.write(':')
    return TimePoint(hours=hours, minutes=minutes, seconds=seconds)

def display_sidebar_width_slider():
    #st.sidebar.text("Width of video")
    st.sidebar.markdown("### Width of video")
    width = st.sidebar.slider(
        label="Width of video", min_value=25, max_value=100,
        value=config.DEFAULT_VIDEO_WIDTH, format="%d%%",
        label_visibility='collapsed')
    return width

def display_video(video, width, seconds):
    st.markdown(f'## {os.path.basename(video)}')
    margin = max((100 - width), 0.01)
    container, _ = st.columns([width, margin])
    container.video(video, start_time=seconds)

def display_timeframe_slider():
    video = st.session_state.video
    return st.slider(label=create_label("Select timeframe"),
                     value=(video.start, video.end),
                     max_value=video.end,
                     step=datetime.timedelta(seconds=1),
                     format='HH:mm:ss',
                     label_visibility='visible')

def display_images(timeframe: 'TimeFrame'):
    video = st.session_state.video
    column_specs = []
    for tp in timeframe.left_context():
        if tp is None:
            column_specs.append(ColumnSpecification(None))
        else:
            image = video.extract_frame_at_second(tp.in_seconds())
            column_specs.append(ColumnSpecification((tp.as_caption(), image)))
    column_specs.append(ColumnSpecification('\<'))
    for tp in timeframe.first_two_timepoints():
        image = video.extract_frame_at_second(tp.in_seconds())
        column_specs.append(ColumnSpecification((tp.as_caption(), image)))
    column_specs.append(ColumnSpecification('\.'))
    for tp in timeframe.last_two_timepoints():
        image = video.extract_frame_at_second(tp.in_seconds())
        column_specs.append(ColumnSpecification((tp.as_caption(), image)))
    column_specs.append(ColumnSpecification('\>'))
    for tp in timeframe.right_context():
        if tp is None:
            column_specs.append(ColumnSpecification(None))
        else:
            image = video.extract_frame_at_second(tp.in_seconds())
            column_specs.append(ColumnSpecification((tp.as_caption(), image)))
    widths = [spec.width for spec in column_specs]
    cols = st.columns(widths)
    for i, spec in enumerate(column_specs):
        if spec.image is not None:
            cols[i].image(spec.image, channels="BGR", caption=spec.caption, width=100)
        else:
            cols[i].write(spec.text)

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

def display_annotation(annotation):
    st.write('')
    st.code(annotation.as_elan())
    df = pd.DataFrame([annotation.as_row()], columns=annotation.columns())
    st.table(df)
    #if annotation.is_valid():
    #    st.json(annotation.as_json())

def display_annotations():
    st.text('All annotations, using order of creation from last to first')
    rows = []
    for annotation in reversed(st.session_state.annotations):
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
    st.info('**Currently available objects**')
    blocks = list(sorted(st.session_state.objects['inplay']))
    st.text('\n'.join(blocks))

def display_action_type_selector(column, key='action_type'):
    label = create_label('Select action type')
    return column.pills(label, config.ACTION_TYPES, key=key)

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


# Actions

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
    pass
    log("Removed  annotation {annotation_id}")

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


# Various other utilities

def get_video_location_from_command_line():
    return sys.argv[1] if len(sys.argv) > 1 else None

def load_annotations():
    filename = st.session_state.io['json']
    video_path = st.session_state.video.path
    with open(filename) as fh:
        raw_annotations = [json.loads(line) for line in fh]
        annotations = []
        for raw_annotation in raw_annotations:
            if 'add-block' in raw_annotation:
                add_block(raw_annotation['add-block'])
            elif 'remove-block' in raw_annotation:
                remove_block(raw_annotation['remove-block'])
            else:
                timeframe = TimeFrame(
                    start=TimePoint(seconds=raw_annotation['start']),
                    end=TimePoint(seconds=raw_annotation['end']))
                annotation = ActionAnnotation(
                    video_path=video_path,
                    timeframe=timeframe,
                    subtype=raw_annotation['action'],
                    args=raw_annotation['arguments'] )
                annotations.append(annotation)
        st.session_state.annotations = annotations
        log(f'Loaded annotations from {filename}')

def annotation_identifiers():
    return [annotation.identifier for annotation in st.session_state.annotations]

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


class TimePoint:

    """Utility class to deal with time points, where a time point refers to an offset
    in the video. It is flexible in that it allows any number of seconds, minutes and
    hours upon initialization, as long as the values are all integers >= 0. It will
    normalize itself to cap seconds and minutes at 59 though."""

    def __init__(self, hours: int = 0, minutes: int = 0, seconds: int = 0):
        if hours < 0 or minutes < 0 or seconds < 0:
            raise ValueError('Values need to be >= 0')
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.normalize()

    def __str__(self):
        cname = self.__class__.__name__
        return f'<{cname} {self.hh()}:{self.mm()}:{self.ss()} {self.in_seconds()}>'

    def hh(self):
        """Return number of hours as a string."""
        return f'{self.hours:02d}'

    def mm(self):
        """Return number of minutes as a string."""
        return f'{self.minutes:02d}'

    def ss(self):
        """Return number of seconds as a string."""
        return f'{self.seconds:02d}'

    def normalize(self):
        """Normalize values so that seconds and minutes are < 60."""
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
        return self.in_seconds() * 1000

    def as_caption(self):
        return str(datetime.timedelta(seconds=self.in_seconds()))

    def adjust_seconds(self, seconds: int):
        """Add seconds to the timepoint and normalize."""
        # TODO: must also know how to deal with values going negative
        self.seconds += seconds
        self.normalize()


class TimeFrame:

    def __init__(self, start: TimePoint, end: TimePoint):
        self.start = start
        self.end = end

    def __str__(self):
        return f'{self.start} ==> {self.end}  [length={len(self)}]'

    def __len__(self):
        return self.end.in_seconds() - self.start.in_seconds()

    def adjust(self, adjust_start: int, adjust_end: int):
        """Adjust the start and end points."""
        self.start.adjust_seconds(adjust_start)
        self.end.adjust_seconds(adjust_end)

    def first_two_timepoints(self):
        start = self.start.in_seconds()
        return (TimePoint(seconds=start), TimePoint(seconds=start + 1))

    def last_two_timepoints(self):
        end = self.end.in_seconds()
        return (TimePoint(seconds=end -1), TimePoint(seconds=end))

    def left_context(self):
        start = self.start.in_seconds()
        context = []
        for s in (start - 2, start - 1):
            try:
                context.append(TimePoint(seconds=s))
            except ValueError:
                context.append(None)
        return context

    def right_context(self):
        end = self.end.in_seconds()
        context = []
        for s in (end + 1, end + 2):
            try:
                context.append(TimePoint(seconds=s))
            except ValueError:
                context.append(None)
        return context


class ColumnSpecification:

    """Utility class to help smoothen putting images in columns."""

    def __init__(self, content):
        self.width = 0
        self.text = None
        self.image = None
        self.caption = None
        if content is None:
            self.width = 2
        elif isinstance(content, str):
            self.width = 1
            self.text = content
        else:
            self.width = 5
            self.caption = content[0]
            self.image = content[1]

    def __str__(self):
        text = str(self.width)
        if self.text:
            text += f' {self.text}'
        if self.caption:
            text += f' {self.caption}'
        return text


class Video:

    """Class to wrap a cv2.VideoCapture instance and add some goodies to it."""

    def __init__(self, video_path: str):
        self.path = video_path
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

    def extract_frames(self, timeframe: TimeFrame):
        pass


class Annotation:

    """Annotations have types (action or gesture) and subtypes (for example, for
    actions we have put and remove). In addition, annotations are intervals so they
    have start and end offsets."""

    def __init__(self, video_path: str, timeframe: TimeFrame,
                 participant: str, subtype: str, args: dict):
        # the type is filled in by the subclass initializer
        self.video_path = video_path
        self.type = None
        self.subtype = subtype
        self.participant = participant
        self.timeframe = timeframe
        self.start = timeframe.start.in_seconds()
        self.end = timeframe.end.in_seconds()
        self.arguments = args
        self.errors = []

    def __str__(self):
        return (
            f'{self.identifier} {self.type}({self.start}, {self.end},' +
            f' {self.participant}, {self.as_formula()})')

    @classmethod
    def columns(cls):
        return []

    def is_valid(self):
        """Checker whether the annotation is not missing any required fields."""
        self.errors = []
        # TODO: add check for out of bounds start or end
        if self.subtype is None:
            self.errors.append(f'WARNING: {self.type} type is not specified')
        for arg_name, arg_value in self.arguments.items():
            if not arg_value:
                self.errors.append(
                    f'WARNING: required argument "{arg_name}" is not specified')
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
        prefix = 'X' if self.subtype is None else self.subtype[0]
        tp = TimePoint(seconds=self.start)
        offset= f'{tp.mm()}{tp.ss()}'
        return f'{prefix}{offset}'

    def as_formula(self):
        formatted_args = ', '.join([f'{a}="{v}"' for a,v in self.arguments.items()])
        return f'{str(self.subtype)}({formatted_args})\n'

    def as_json(self):
        return {
            'identifier': self.identifier,
            'start': self.start,
            'end': self.end,
            'participant': self.participant,
            'action': self.subtype,
            'arguments': self.arguments
        }

    def as_elan(self):
        offsets = f'{self.start}.0\t{self.end}.0'
        return f'ACTION\t{offsets}\t{self.elan_identifier()}: {self.as_formula()}'

    def as_row(self):
        return [self.identifier, self.start_as_string(), self.end_as_string(),
                self.participant, self.type, self.subtype, self.as_formula()]

    def start_as_string(self):
        t = TimePoint(seconds=self.start)
        return f'{t.mm()}:{t.ss()}'

    def end_as_string(self):
        t = TimePoint(seconds=self.end)
        return f'{t.mm()}:{t.ss()}'

    def save(self):
        if self.is_valid():
            st.session_state.annotations.append(self)
            json_file = st.session_state.io['json']
            elan_file = st.session_state.io['elan']
            with open(json_file, 'a') as fh:
                fh.write(json.dumps(self.as_json()) + '\n')
            with open(elan_file, 'a') as fh:
                fh.write(self.as_elan())
            st.session_state.action_type = None
            log(f'Saved annotation {self.identifier} {self.as_formula()}')
        st.session_state.errors = self.errors
        for error in self.errors:
            log(error)


class GestureAnnotation(Annotation):

    identifier = 0

    def __init__(self, video_path: str, start: int, end: int,
                 participant: str, subtype: str, args: list):
        self.identifier = self.get_identifier()
        super().__init__(
            video_path=video_path, start=start, end=end,
            participant=participant, subtype=subtype, args=args)
        self.type = 'gesture'

    def get_identifier(self):
        self.__class__.identifier += 1
        return f'g{self.__class__.identifier:04d}'


class ActionAnnotation(Annotation):

    # TODO: we now get gaps when we fail to add an annotation, maybe assign
    # identifier when we add the annotation (after testing for validity), or
    # else go back to using an identifier created from a timestamp.

    identifier = 0

    def __init__(self, video_path: str, timeframe: TimeFrame, subtype: str, args: list):
        self.identifier = self.get_identifier()
        super().__init__(
            video_path=video_path, timeframe=timeframe,
            participant='Builder', subtype=subtype, args=args)
        self.type = 'action'

    @classmethod
    def columns(cls):
        return ['id', 'start', 'end', 'participant', 'type', 'subtype', 'formula']

    def get_identifier(self):
        self.__class__.identifier += 1
        return f'a{self.__class__.identifier:04d}'


