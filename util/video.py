import os
import time
import asyncio
import datetime
import functools

import cv2
import numpy as np
import streamlit as st

from util.cache import ImageCache
import util


@functools.total_ordering
class TimePoint:

    """Utility class to deal with time points, where a time point refers to an offset
    in the video. It is flexible in that it allows any number of seconds, minutes and
    hours upon initialization, as long as the values are all integers >= 0. It will
    normalize itself to cap seconds and minutes at 59 though."""

    @classmethod
    def from_date(cls, d: datetime.datetime):
        t = d.time()
        ms = t.microsecond // 1000
        return cls(
            hours=t.hour, minutes=t.minute, seconds=t.second, milliseconds=ms)

    @classmethod
    def from_time(cls, t: datetime.time):
        ms = t.microsecond // 1000
        return cls(
            hours=t.hour, minutes=t.minute, seconds=t.second, milliseconds=ms)

    @classmethod
    def from_updated_timepoint(cls, timepoint: 'TimePoint', milliseconds: int):
        """Takes a TimePoint and returns a new one which is the same except that the
        specified amount of millicesonds is added."""
        # TODO: not currently used and probably deprecated
        total = timepoint.in_milliseconds() + int(milliseconds)
        return cls(milliseconds=total)

    def __init__(self, hours=0, minutes=0, seconds=0, milliseconds=0):
        # if hours < 0 or minutes < 0 or seconds < 0 or milliseconds < 0:
        #    raise ValueError('Values need to be >= 0')
        # print('===', hours, minutes, seconds, milliseconds)
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

    def timestamp(self, short=False) -> str:
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
            # We do not check whether the end of a timeframe is after the start,
            # but len() may not return a negatove number so making sure we do
            # not do that.
            # TODO: should not even allow this to happen
            return max(self.end.in_seconds() - self.start.in_seconds(), 0)
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
        # TODO: did not feel the need to use FrameCollector, could be wrong
        # TODO: this seems to be deprecated and should be on Video class anyway
        return Frame(self.video, milliseconds, st.session_state.cache)

    def slice_to_left(self, milliseconds: int, n=4, step=100):
        return collect_frames(video, range(n * -step, 0, step))

    def slice_to_right(self, milliseconds: int, n=4, step=100):
        return collect_frames(video, range(0, n * step, step))


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
        videos cannot be longer than 24 hours)."""
        fps = self.vidcap.get(cv2.CAP_PROP_FPS)
        frame_count = int(self.vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        seconds = frame_count / fps
        #st.write(seconds)
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

    def __init__(self, vidcap, cache: ImageCache, offset: int):
        self.vidcap = vidcap
        self.timepoint = TimePoint(milliseconds=offset)
        if offset in cache:
            image = cache[offset]
        else:
            image = self.get_frame(offset)
            cache[offset] = image
        self.image = image
        self.success = False if self.image is None else True

    def __str__(self):
        timestamp = self.timepoint.timestamp()
        return f'<{self.__class__.__name__} t={timestamp} image={self.success}>'

    def get_frame(self, offset: int) -> np.ndarray:
        util.debug(f'Extracting frame at {offset} from video')
        return self.vidcap.extract_frame(offset)

    def caption(self, short=True):
        return self.timepoint.timestamp(short=short)


class FrameCollector:

    """Class that wraps frame retrieval from the video in asynchronous calls."""

    # TODO: may want to use an asyncio timeout. Some errors may make this code hang
    # and just not return anything. See the following for some background:
    # https://betterstack.com/community/guides/scaling-python/python-timeouts/

    def __init__(self, vidcap, cache: ImageCache):
        self.vidcap = vidcap
        self.cache = cache
        self.frames = []

    async def get_frames(self, timepoints: list, timing=False):
        util.debug(f'FrameCollector.get_frames({str(timepoints)})')
        t0 = time.time()
        self.timepoints = timepoints
        calls = (self.get_frame(tp) for tp in timepoints)
        util.debug('    await asyncio.gather(*calls) STARTED')
        results = await asyncio.gather(*calls)
        util.debug('    await asyncio.gather(*calls) ENDED')
        if timing:
            print(f"Got {len(timepoints)} frames in {time.time() - t0} seconds")
        return results

    async def get_frame(self, tp: int):
        return Frame(self.vidcap, self.cache, tp)


def collect_frames(video, frame_offsets: list):
    # TODO: probably add this to the video class
    fc = FrameCollector(video, st.session_state.cache)
    frames = asyncio.run(fc.get_frames(frame_offsets))
    return frames


'EOF'
