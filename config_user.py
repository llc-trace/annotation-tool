
TITLE = "Leave/Return Annotator"

def create_object_pool():
    return set()



TYPES = {
	'Object': ['marble','box','basket'],
	'Location': ['room']
}


OBJECTS = TYPES['Object']
LOCATIONS = TYPES['Location']


OBJECT_LABEL = '**Object** (select from list or define your own)'
LOCATION_LABEL = '**Location** (select from list or define your own)'
SOURCE_LABEL = '**Source** (select from list or define your own)'
DESTINATION_LABEL = '**Destination** (select from list or define your own)'


PREDICATES = {

	'OPEN': [
		{'type': 'Person', 'label': '**Person**', 'items': ['TEXT']},
		{'type': 'Object', 'label': OBJECT_LABEL, 'items': [OBJECTS, 'TEXT']}],

	'CLOSE': [
		{'type': 'Person', 'label': '**Person**', 'items': ['TEXT']},
		{'type': 'Object', 'label': OBJECT_LABEL, 'items': [OBJECTS, 'TEXT']}],

	'LEAVE': [
		{'type': 'Person', 'label': '**Person**', 'items': ['TEXT']},
		{'type': 'Location', 'label': LOCATION_LABEL, 'items': [LOCATIONS, 'TEXT']}],

	'RETURN': [
		{'type': 'Person', 'label': '**Person**', 'items': ['TEXT']},
		{'type': 'Location', 'label': LOCATION_LABEL, 'items': [LOCATIONS, 'TEXT']}],

	'MOVE': [
		{'type': 'Person', 'label': '**Person**', 'items': ['TEXT']},
		{'type': 'Object', 'label': OBJECT_LABEL, 'items': [OBJECTS, 'TEXT']},
		{'type': 'Source', 'label': SOURCE_LABEL, 'items': [LOCATIONS, 'TEXT']},
		{'type': 'Destination', 'label': DESTINATION_LABEL, 'items': [LOCATIONS, 'TEXT']}],

	# initial experiment to see how we can deal with open-ended predicate lists
    'OTHER': [
        {'type': 'name', 'label': '**Predicate**', 'items': ['TEXT']},
        {'type': 'ARG0', 'label': '**ARG0**', 'items': ['TEXT']},
        {'type': 'ARG1', 'label': '**ARG1**', 'items': ['TEXT']},
        {'type': 'ARG2', 'label': '**ARG2**', 'items': ['TEXT']}],

}
