
DEFAULT_VIDEO_WIDTH = 50	# width in percentage of total width
DEFAULT_IMAGE_WIDTH = 100	# width in pixels

PARTICIPANTS = ('Director1', 'Director2', 'Director3', 'Builder')

ACTION_TYPES = {
	'PUT': ['Object', 'Location'],
	'REMOVE': ['Object', 'Location'],
	'MOVE': ['Object', 'Source', 'Destination'],
	'TURN': ['Object'] }

GESTURE_TYPES = {
	'POINT': ['Direction'],
	'PUSH-LEFT': [],
	'PUSH-RIGHT': []}
