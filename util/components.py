"""

Components always include one or more Streamlit widgets. Optionally they can
return any object with user choices.

All components have access to the streamlit instance and its session state.

In most cases the caller is responsible for handing in a uniqe key if it is needed.

"""

import streamlit as st

import util
from util.video import collect_frames, TimePoint, TimeFrame
from util import streamlit as stutil
from config import default as config


def predicate_selector(key=None) -> str:
    """
    Displays the predicate names from the configuration as Streamlit pills
    and returns the predicate that was selected by the user. The label is fixed
    to be 'Select predicate'.
    """
    label = util.create_label('Select predicate')
    return st.pills(label, config.PREDICATES.keys(), key=key)


def timeframe_selector(settings: dict) -> TimeFrame:
    """
    Display the widgets needed to select a timeframe. This includes widgets to
    create timestamps and video frame images.

    ── timeframe_selector
       ├── timestamp_selector
       ├── timestamp_selector
       ├── video_frames
       └── video_frames
    """
    with st.container(border=True):
        st.markdown('**Select start and end in hh:mm:ss:mmm**')
        keys1 = ['start_hh', 'start_mm', 'start_ss', 'start_mmm']
        keys2 = ['end_hh', 'end_mm', 'end_ss', 'end_mmm']
        col1, col2 = st.columns(2)
        with col1:
            tp1 = timestamp_selector('Start', keys=keys1)
            st.write(tp1)
        with col2:
            tp2 = timestamp_selector('End', keys=keys2)
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
        if not settings['hide_boundaries']:
            video_frames(tf, tf.start)
            video_frames(tf, tf.end)
    return tf


def timestamp_selector(header: str, keys: list):
    """
    Display a widget to pick a timestamp. The header and the list of keys make sure
    that each number_input created has a unique key.
    """
    # TODO: this is similar to stutil.sidebar_display_seek_inputs(), those two
    # should be combined
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


def video_frames(timeframe: TimeFrame, timepoint: TimePoint, header=None) -> None:
    """
    Displays the video frame thumbnails for a list of time points, they will be
    aligned horizontally in a box without a border.
    """
    window = util.get_window(timepoint.in_milliseconds())
    frames = collect_frames(timeframe.video, window)
    with st.container(border=False):
        if header is not None:
            st.write(header)
        cols = st.columns(len(frames))
        for i, frame in enumerate(frames):
            caption = None
            if timepoint.in_milliseconds() == frame.timepoint.in_milliseconds():
                caption = '✔︎'
            with cols[i]:
                captioned_video_frame(frame, caption=caption)


def video_frames_from_list(frames, cols=10, header=None):
    """
    Display frames horizontally in a bordered box, frames all have a timestamp
    as a caption.
    """
    # TODO: maybe merge this with video_frames()
    with st.container(border=True):
        if header is not None:
            st.write(header)
        cols = st.columns(cols)
        for i, frame in enumerate(frames):
            with cols[i]:
                captioned_video_frame(frame)


def captioned_video_frame(frame, caption=None):
    """
    Displays a video frame with a caption. If the caption is None than the defualt
    caption will be used, which is the timestamp of the frame.
    """
    caption = frame.caption() if caption is None else caption
    if frame.success:
        st.image(frame.image, channels="BGR", caption=caption)
    else:
        # TODO: on failure may want to pass in an empty image with a caption like
        # below, but before that need to figure out how to control the size of the
        # image better (that is make it match the video screen dimensions).
        # svg = (
        #     '<svg width="100" height="75" xmlns="http://www.w3.org/2000/svg">'
        #     '<rect width="100" height="75" /></svg>')
        # column.image(svg, caption=caption)
        pass


def timeframe_loop(video, width, annotation, identifier=0) -> None:
    """
    Adds the button that starts a loop over the annotation timeframe. The identifier
    is only needed if you have more than one buttons on the page. What it does is adding
    some whitespace padding to the end of the button label, which makes the label unique,
    but it does not change the display.
    """
    if len(annotation.timeframe) > 0:
        start = max(0, annotation.timeframe.start.in_seconds() - 1)
        end = annotation.timeframe.end.in_seconds() + 1
        postfix = ' ' * identifier
        play = st.button(f"Loop video from {start} to {end}{postfix}")
        if play:
            st.button(f"Stop loop{postfix}")
            stutil.display_video(
                video, width, start_time=start, end_time=end, loop=True, autoplay=True)
