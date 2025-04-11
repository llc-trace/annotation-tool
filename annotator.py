"""

Timeline Annotator

Originally created for Action and Gesture annotation for the TRACE project.

To run this:

$ pip install -r requirements.txt
$ streamlit run annotator.py <VIDEO_FILE> <TASK_CONFIG_FILE> [debug]

"""

import streamlit as st

from config import default as config
import util
import util.streamlit as stutil
from util.video import TimePoint, TimeFrame
from util import components, actions


st.set_page_config(page_title=config.TITLE, layout="wide")

stutil.intialize_session_state()
video = st.session_state.video


# SIDEBAR

# The sidebar prints some info and has a variety of controls

st.sidebar.title(config.TITLE)
stutil.sidebar_display_info()
mode = stutil.sidebar_display_tool_mode()
if 'annotation' in mode:
    offset, width = stutil.sidebar_display_video_controls()
if mode == 'add annotations':
    add_annotation_settings = stutil.sidebar_display_annotation_controls()
if mode == 'show annotations':
    show_annotations_settings = stutil.sidebar_display_annotation_list_controls()
if mode == 'dev':
    dev = stutil.sidebar_display_dev_controls()
    st.write(dev)
    clear_cache = st.sidebar.button(
        'Clear image cache', on_click=actions.clear_image_cache)


# MAIN CONTENT

if mode == 'add annotations':

    st.title('Add annotations')
    st.info(f'**{video.filename}**')
    stutil.display_video(video, width, start_time=offset.in_seconds())

    # The box with timeframe selection widgets
    tf = components.timeframe_selector(add_annotation_settings)

    # A button to loop the video for the currently selected timeframe
    components.timeframe_loop(video, width, st.session_state.annotation)

    # The box with the predicate and the argument structure
    with st.container(border=True):
        args1 = None
        args2 = None
        use_conjunction = st.checkbox('Use Conjunction', key='opt_conjunction')
        predicate1 = components.predicate_selector(key='predicate_type_1')
        # util.PredicateDescription(predicate).pp()
        arguments1 = config.PREDICATES.get(predicate1, [])
        args1 = stutil.display_arguments(predicate1, arguments1)
        args1 = util.process_arguments(args1)
        if use_conjunction:
            st.divider()
            predicate2 = components.predicate_selector(key='predicate_type_2')
            # util.PredicateDescription(predicate).pp()
            arguments2 = config.PREDICATES.get(predicate2, [])
            args2 = stutil.display_arguments(predicate2, arguments2, True)
            args2 = util.process_arguments(args2)

    # The boxes with the tier and the properties, if relevant. Don't show them
    # until after predicate selection, which structures the annotation but also
    # solved an issue with refreshing the properties after an annotation was saved.
    selected_tier = None
    if predicate1:
        if config.TIER_IS_DEFINED_BY_USER:
            with st.container(border=True):
                selected_tier = stutil.display_tier()
        with st.container(border=True):
            properties = config.PROPERTIES
            props = stutil.display_properties(properties)
            props = util.process_arguments(props)
    else:
        props = {}

    # Now that we have our values we can update the annotation
    annotation = st.session_state.annotation
    if not use_conjunction:
        annotation.set_predicate(predicate1, args1)
    else:
        annotation.set_lf(predicate1, args1, predicate2, args2)
    annotation.properties = props
    annotation.calculate_tier(tf, selected_tier)

    # Display the updated annotation with a save button or a warning
    with st.container(border=True):
        stutil.display_annotation(annotation, add_annotation_settings)
    if annotation.is_valid():
        st.button("Save Annotation", on_click=annotation.save)
    else:
        st.markdown(
            "*Cannot add annotation yet because not all required fields have"
            " been specified and/or not all values are legal.*")
        show_issues = st.button("Show issues")
        if show_issues:
            for e in annotation.errors:
                st.info(e)
    stutil.display_errors()


if mode == 'show annotations':

    st.title('Annotations')
    st.info(f'**{video.filename}**')
    if not show_annotations_settings['hide-video']:
        stutil.display_video(video, width, start_time=offset.in_seconds())
    fname = st.session_state.io['json']

    action = st.pills(
        'annotation controls',
        options=[
            'Reload annotations',
            'Remove annotation',
            'Export annotations in ELAN format'],
        label_visibility='collapsed')

    if action is not None:
        if action.startswith('Remove'):
            annotation_id = stutil.display_remove_annotation_select()
            st.button(
                'Remove',
                on_click=actions.remove_annotation,
                args=[annotation_id])
        elif action.startswith('Reload'):
            util.annotation.load_annotations()
            st.info('Annotations were reloaded')
            if st.session_state.errors:
                for error in st.session_state.errors:
                    st.warning(error)
                st.session_state.errors = []
        elif action.startswith('Export'):
            util.annotation.export_annotations()
            st.info(f'Annotations were exported to {st.session_state.io["elan"]}')

    stutil.display_messages()
    stutil.display_annotations(show_annotations_settings)


if mode == 'show object pool':

    st.title('Object Pool')
    pool = st.session_state.pool
    object_types = st.session_state.pool.object_types

    if object_types:
        st.write(pool)
        tabs = st.tabs(object_types)
        for i in range(len(tabs)):
            with tabs[i]:
                obj_type = object_types[i]
                available = pool.get_available(obj_type)
                inplay = pool.get_in_play(obj_type)
                st.text(
                    f'There are {len(available) + len(inplay)} {obj_type} in the pool, '
                    f'{len(available)} are available and {len(inplay)} are in use')
                label = f'Select {obj_type} from the pool to put in use'
                st.write(label)
                c1, c2, _ = st.columns([4, 2, 6])
                selected = c1.multiselect(label, available, label_visibility='collapsed')
                c2.button(f"Add {obj_type}",
                          on_click=actions.add_objects,
                          args=[obj_type, selected])
                label = f'Stop using {object_types[i]} and put them back in the pool'
                st.write(label)
                c3, c4, _ = st.columns([4, 2, 6])
                selected = c3.multiselect(label, inplay, label_visibility='collapsed')
                c4.button(
                    f"Remove {obj_type}",
                    on_click=actions.remove_objects,
                    args=[obj_type, selected])
                stutil.display_messages()
                stutil.display_available_objects(obj_type)
    else:
        st.text('The Object Pool is not used for this task.')

    # blocks_to_add = stutil.display_add_block_select(c1)
    # c2.button("Add", on_click=actions.add_blocks, args=[blocks_to_add])
    # block_to_remove = stutil.display_remove_block_select(c3)
    # c4.button("Remove", on_click=actions.remove_block, args=[block_to_remove])


if mode == 'help':

    st.title('Annotation tool help')
    url = 'https://github.com/llc-trace/annotation-tool/blob/main/docs/manual/index.md'
    st.markdown(f'For help see the manual at [{url}]({url}).')


if mode == 'dev':

    st.title('Developer goodies')
    if dev == 'Show session_state':
        with st.container(border=True):
            st.markdown('**Session State**')
            st.write(st.session_state)
    elif dev == 'Show config settings':
        with st.container(border=True):
            st.markdown('#### Configurations settings - default')
            with open('config/default.py') as fh:
                st.code(fh.read(), language='python')
        with st.container(border=True):
            st.markdown('#### Configurations settings - task specific')
            with open(st.session_state.io['config_path']) as fh:
                st.code(fh.read(), language='python')
    elif dev == 'Show objects pool':
        with st.container(border=True):
            st.markdown('**Objects Pool**')
            st.write(st.session_state.pool.as_json())
    elif dev == 'Show log':
        with open(st.session_state.io['log']) as fh:
            with st.container(border=True):
                st.markdown('**Log contents**')
                st.code(fh.read(), language=None)
    elif dev == 'Show predicate specifications':
        with st.container(border=True):
            st.markdown('**Predicate-argument specifications**')
            st.write(config.PREDICATES)
    elif dev == 'Show property specifications':
        with st.container(border=True):
            st.markdown('**Property specifications**')
            st.write(config.PROPERTIES)
    elif dev == 'Show image cache':
        with st.container(border=True):
            st.markdown('**Image cash**')
            timepoints = [str(tp) for tp in sorted(st.session_state.cache.data)]
            tp = st.pills('imagecash-timepoint', timepoints, label_visibility='collapsed')
            if tp is not None:
                st.image(st.session_state.cache[int(tp)], channels='BGR')
    elif dev == 'Show annotations':
        with st.container(border=True):
            st.markdown('**Annotations**')
            annotations = st.session_state.annotations
            name_index = {a.name: a for a in annotations}
            id_index = {a.identifier: a for a in annotations}
            name_choice = st.radio(
                'dev-radio', ['by identifier', 'by name'],
                horizontal=True, label_visibility='collapsed')
            if name_choice == 'by name':
                annos = [anno.name for anno in sorted(annotations)]
            else:
                annos = sorted([anno.identifier for anno in annotations])
            id_or_name = st.pills('dev-annotations', annos, label_visibility='collapsed')
            if id_or_name is not None:
                if name_choice == 'by name':
                    selected = name_index.get(id_or_name)
                else:
                    selected = id_index.get(id_or_name)
                st.write(selected)
                st.code(selected.as_yaml(), language='yaml')
                st.write(selected.as_json())
