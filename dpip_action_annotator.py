import streamlit as st

import config
import utils


video = '/Users/Shared/archive/video/cpb-aacip-507-z31ng4hp5t.part.mp4'

st.set_page_config(page_title="DPIP Action Annotator", layout="wide")

if not 'annotations' in st.session_state:
    st.session_state['annotations'] = []
if not 'errors' in st.session_state:
    st.session_state.errors = []

# Sidebar controls the timepoint in the video and the number of thumbnails
st.sidebar.markdown('# BPIP Action Annotation')
seconds = st.sidebar.number_input('Time offset in seconds', key="seconds", value=0, min_value=0)
thumbnails = st.sidebar.number_input('Number of thumbnails', key="thumbnails", value=8, min_value=0)
st.sidebar.text(f'Number of annotations: {len(st.session_state.annotations)}')

# displays the video title, the video itself and the thumbnails
utils.display_video(video, seconds, thumbnails, st)

col1, col2, col3, col4 = st.columns([1,1,4,8])
with col1:
    start = st.number_input('start', value=0, min_value=0)
with col2:
    end = st.number_input('end', value=0, min_value=0)
with col3:
    action_type = st.selectbox("action type", config.ACTION_TYPES, index=None)
with col4:
    action_args = utils.action_arguments(action_type)
    args = utils.display_arguments(action_args, st)

annotation = utils.ActionAnnotation(start, end, action_type, args)
st.info(annotation)
st.button("Add Action Annotation", on_click=annotation.save, args=[seconds, st])

utils.display_errors(st)
st.divider()
utils.display_annotations(st)

