# Further developing the annotation tool

Various notes on things to do and observations made. Some up-to-date, some hopelessly deprecated.


## Special properties (task and tier)

These are not like the other ones in that they are required for the tool to work and they really say more about the place/environment of the annotation than the annotation itself.

Annotations are organized in tasks and tiers. Tasks are the biggest granularity. Any annotation has to be in a task. Tiers are the next level. In a task you have one or more tiers and each annotation is in a tier.

I made the decision to allow more than one task in the annotations file of a video (maybe not so smart really). With that the current format of the annotations needs to change because when loading the annotations and other instructions we really need to know what task and tier they fall. The tier is in the properties dictionary, but should probably be put at the top level.

Here are two fragments from an annotation file with an instruction to add a block and an annotation definition (the latter not on one line as it should be but formatted for readability:

```json
{"add-block": "SmallRedBlock1"}
```
```json
{
  "identifier": "a0001",
  "name": "T0005",
  "start": 5000,
  "end": 12000,
  "predicate": "TURN",
  "arguments": {
    "Object": "LargeYellowBlock1"
  },
  "properties": {
    "tier": "ACTION1"
  }
}
```

For the instruction we just want to add the task, the tier is not needed because this is not an annotation:


```json
{ "task": "Actions", "add-block": "SmallRedBlock1" }
```

And for the annotation we add the task and move the annotation:

```json
{
  "task": "Actions",
  "tier": "ACTION1",  
  "identifier": "a0001",
  "name": "T0005",
  "start": 5000,
  "end": 12000,
  "predicate": "TURN",
  "arguments": {
    "Object": "LargeYellowBlock1"
  },
  "properties": {}
}
```

For the Annotation instance we add a task field.


### Legacy annotations

We could have annotations like this

```json
{"add-block": "LargeBlueBlock1"}
{"add-block": "LargeYellowBlock1"}
{"add-block": "SmallRedBlock1"}
{"identifier": "a0001", "name": "T0005", "start": 5000, "end": 12000, "predicate": "TURN", "arguments": {"Object": "LargeYellowBlock1"}, "properties": {"tier": "ACTION1"}}
{"identifier": "a0002", "name": "T0340", "start": 220000, "end": 236000, "predicate": "TURN", "arguments": {"Object": "SmallRedBlock1"}, "properties": {"tier": "ACTION1"}}
{"identifier": "a0003", "name": "P0334", "start": 214000, "end": 224000, "predicate": "PUT", "arguments": {"Object": "SmallRedBlock1", "Location": "above(LargeYellowBlock1)"}, "properties": {"tier": "ACTION2"}}
{"identifier": "a0004", "name": "e0027", "start": 27000, "end": 34000, "predicate": "emblem-GA", "arguments": {"ARG0": "Director1", "ARG1": "a", "ARG2": "b"}, "properties": {"tier": "GESTURES-Director1", "comment": null}}
{"identifier": "a0005", "name": "i0046", "start": 46000, "end": 58000, "predicate": "icon-GA", "arguments": {"ARG0": "Builder", "ARG1": "x", "ARG2": "(a / actor)"}, "properties": {"tier": "GESTURES-Builder", "comment": null}}
{"task": "Actions", "tier": "Actions", "identifier": "a0006", "name": "L0036", "start": 36000, "end": 242000, "predicate": "LEAVE", "arguments": {"Person": "se", "Location": "room"}, "properties": {}}
```

We have a mix of lines with and without top-level task and tier properties. When loading some default should be filled in.


### Collecting tasks

I want to load a task from disk:

1. find the tasks in the config directory, or maybe in a tasks directory
2. do the task specific import (potentially tricky because you have to undo a previous load)
3. instead of the previous, walk away from the import-based approach and use Yaml configuration files.


Initial code to find a task in the config directory:

```python
import pathlib

tasks = {}
for f in pathlib.Path('config').iterdir():
	if f.name in ('__init__.py', 'default.py'):
		continue
	if f.is_file() and f.suffix == '.py':
		#print(type(f), f.name)
		with f.open() as fh:
			for line in fh.readlines():
				line = line.strip()
				if line.startswith('TASK =') or line.startswith('TASK='):
					# this will break down when a comment follows the line
					# look into using pyparsing
					task = line.split('=', 1)[1].strip()
					task = task.strip('\"\'')
					#print(f'TASK = {task}')
					tasks[task] = f
for task in sorted(tasks):
	print(f'{task}')
```

This is all very low priority.


## Adding Gesture annotation

Taken from  Multimodal\_AMR\_Annotation\_Guidelines\_20220914.pdf:

There are three kinds of gestures:

| gesture  | description |
| :------- | :----------- |
| Iconic   | Gestures that model the shape of an object or the motion of an action. |
| Deictic  | Refers to familiar pointing, indicating objects in conversational space. |
| Emblem   | Gestures with standard properties and language-like features. |

Examples:

- a speaker arcs his/her fist to form a cup and drink from it when saying ‘I drink from a cup’ (iconic)
- a speaker says ‘I walked up the stairs’, he/she points upward (deictic)
- the OK sign has a culturally agreed upon meaning; and it is necessary to place the thumb and index finger together in order to form the sign (emblem)

Gestures have an canonical template:

```
(g / [gesture]-GA
  :ARG0 (s / signaler)
  :ARG1 [content]
  :ARG2 (a / actor))
```

ARG0 and ARG2 correspond to the gesturer and addressee. ARG1, the semantic content of the gesture, varies by gesture type.

| gesture         | ARG1        |
| :-------------- | :---------- |
| Iconic gesture  | The object or action being modeled. |
| Deictic gesture | The object or location being pointed to. |
| Emblem          | The conventional, culturally agreed- upon meaning of the gesture. |
