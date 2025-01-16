import streamlit as st

import config
import utils


video = '/Users/Shared/archive/video/cpb-aacip-507-z31ng4hp5t.part.mp4'

st.set_page_config(page_title="DPIP Gesture Annotator", layout="wide")

if not 'annotations' in st.session_state:
    st.session_state['annotations'] = []
if not 'errors' in st.session_state:
    st.session_state.errors = []

# Sidebar controls the timepoint in the video and the number of thumbnails
st.sidebar.markdown('# BPIP Gesture Annotation')
seconds = st.sidebar.number_input('Time offset in seconds', key="seconds", value=0, min_value=0)
thumbnails = st.sidebar.number_input('Number of thumbnails', key="thumbnails", value=8, min_value=0)
st.sidebar.text(f'Number of annotations: {len(st.session_state.annotations)}')

# displays the video title, the video itself and the thumbnails
utils.display_video(video, seconds, thumbnails, st)

col1, col2, col3, col4, col5 = st.columns([2.5,1,1,3,8])
with col1:
    participant = st.selectbox('participant', config.PARTICIPANTS, index=None)
with col2:
    start = st.number_input('start', value=0, min_value=0)
with col3:
    end = st.number_input('end', value=0, min_value=0)
with col4:
    gesture_type = st.selectbox("gesture type", config.GESTURE_TYPES, index=None)
with col5:
    gesture_args = utils.gesture_arguments(gesture_type)
    args = utils.display_arguments(gesture_args, st)

annotation = utils.GestureAnnotation(start, end, participant, gesture_type, args)
st.info(annotation)
st.button("Add Gesture Annotation", on_click=annotation.save, args=[seconds, st])

utils.display_errors(st)
st.divider()
utils.display_annotations(st)

