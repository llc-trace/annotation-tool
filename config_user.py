
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

	'MOVE': [
		{'type': 'Person', 'label': '**Person**', 'items': ['TEXT']},
		{'type': 'Object', 'label': OBJECT_LABEL, 'items': [OBJECTS, 'TEXT']},
		{'type': 'Source', 'label': '**Source**', 'items': [LOCATIONS, 'TEXT']},
		{'type': 'Destination', 'label': '**Destination**', 'items': [LOCATIONS, 'TEXT']},
	]

}