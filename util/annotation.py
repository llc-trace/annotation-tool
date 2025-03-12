import os
import json
import pathlib
import functools
from copy import deepcopy

import streamlit as st

from config import default as config
from util.video import TimePoint, TimeFrame
import util


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
        annotations = [a for a in annotations if a.identifier not in removed_annotations]
        st.session_state.annotations = annotations
        util.log(f'Loaded annotations from {filename}')


def annotation_identifiers() -> list:
    return [annotation.identifier for annotation in st.session_state.annotations]


def overlap(tf1: 'TimeFrame', tf2: 'TimeFrame'):
    """Return True if two time frames overlap, False otherwise."""
    # TODO: mayhap put this on the TimeFrame class
    if tf1.end <= tf2.start:
        return False
    if tf2.end <= tf1.start:
        return False
    return True


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
                util.log(f'{obj} was already put in play')
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
                util.log(f'{obj} was already removed from play')
            self.objects[obj_type]['available'].add(obj)

    def as_json(self):
        pool = {}
        for obj_type, data in self.objects.items():
            pool[obj_type] = data
        return pool


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
            f'{self.task} {self.tier} {self.identifier} {self.name}'
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
            offset = f'{tp.mm()}{tp.ss()}'
            return f'{prefix}{offset}'
        except Exception:
            return None

    def as_formula(self):
        formatted_args = ', '.join([f'{a}="{v}"' for a, v in self.arguments.items()])
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
            taken = util.current_timeframes(self.task)
            for name, taken_tf in taken:
                if overlap(tf, taken_tf):
                    self.tier = config.TIERS[1]
                    return
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
            util.log(f'Saved annotation {self.identifier} {self.as_formula()}')
        st.session_state.errors = self.errors
        st.session_state.opt_show_boundary = False
        st.session_state.annotation = Annotation()
        for error in self.errors:
            util.log(error)
