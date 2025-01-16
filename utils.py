import datetime

import cv2


## cv2 utilities

def extract_frame(vidcap, timepoint: int):
    vidcap.set(cv2.CAP_PROP_POS_MSEC, timepoint)
    success, image = vidcap.read()
    if success:
        image_file_name = f"images/frame-{timepoint:09d}.jpg"
        cv2.imwrite( image_file_name, image)
        return image_file_name
    return None

## Streamlit display utilities

def display_video(video, seconds, thumbnails, st):
    st.markdown(f'##### {video}')
    st.video(video, start_time=seconds)
    vidcap = cv2.VideoCapture(video)
    display_images(vidcap, seconds, thumbnails, st)

def display_image(vidcap, seconds, st):
    milliseconds = int(seconds * 1000)
    st.text(f'Showing video at {seconds} seconds')
    image_file = extract_frame(vidcap, milliseconds)
    st.image(image_file, width=150)

def display_images(vidcap, seconds: int, n: int, st):
    milliseconds = seconds * 1000
    cols = st.columns(n)
    for i in range(n):
        with cols[i]:
            image_file = extract_frame(vidcap, milliseconds + (i * 1000))
            #st.image(image_file, caption=seconds+i)
            st.image(image_file, str(datetime.timedelta(seconds=seconds+i)))

def display_arguments(arguments: list, st):
    if arguments:
        cols = st.columns(len(arguments))
        args = [''] * len(arguments)
        for i, arg in enumerate(arguments):
            with cols[i]:
                args[i] = st.text_input(arg)
        return zip(arguments, args)
    return []

def display_annotations(st):
    # not using the Annotation instances to avoid warnings
    printable = [str(a) for a in reversed(st.session_state.annotations)]
    st.text('Current annotations')
    st.table(printable)

def display_errors(st):
    for error in st.session_state.errors:
        st.error(error)

# Utilities to generate templates for annotations, these contain argument
# information for all possible relations.

def action_arguments(action_type: str):
    if action_type in ('put', 'remove'):
        return ['Object', 'Location']
    elif action_type == 'move':
        return ['Object', 'Source', 'Destination']
    else:
        return []

def gesture_arguments(gesture_type: str):
    if gesture_type == 'point':
        return ['Direction']
    else:
        return []


class Annotation:

    """Annotations have types (action or gesture) and subtypes (for example, for
    actions we have put and remove). In addition, annotations are intervals so they
    have start and end offsets."""

    def __init__(self, start: int, end: int, participant: str, subtype: str, args: list):
        # the type is filled in by the subclass initializer
        self.type = None
        self.subtype = subtype
        self.participant = participant
        self.start = start
        self.end = end
        self.args = list(args)
        self.arg_names = tuple([a[0] for a in self.args])
        self.arg_values = tuple([a[1] for a in self.args])
        self.formula = f'{self.type}({", ".join(self.arg_values)})'
        self.errors = []

    def __str__(self):
        return f'{self.type}({self.start}, {self.end}, {self.participant}, {self.formula})'

    def is_valid(self, current_index: int):
        # the current_index is handed in by the application and it refers to what timepoint the
        # first thumbnail points at.
        self.errors = []
        for arg_name, arg_value in zip(self.arg_names, self.arg_values):
            if not arg_value:
                self.errors.append(f'ERROR: required argument "{arg_name}" is not specified')
        if self.start > self.end:
            self.errors.append('ERROR: the start of the interval cannot be before the end')
        return True if not self.errors else False

    def save(self, current_index, st):
        if self.is_valid(current_index=current_index):
            st.session_state.annotations.append(self)
        st.session_state.errors = self.errors


class GestureAnnotation(Annotation):

    def __init__(self, start: int, end: int, participant: str, subtype: str, args: list):
        super().__init__(start=start, end=end, participant=participant, subtype=subtype, args=args)
        self.type = 'gesture'


class ActionAnnotation(Annotation):

    def __init__(self, start: int, end: int, subtype: str, args: list):
        super().__init__(start=start, end=end, participant='Builder', subtype=subtype, args=args)
        self.type = 'action'
