# Expanding on the Predicates

In [issue 33](https://github.com/llc-trace/annotation-tool/issues/33) there is a push for allowing things like

```
PUT(obj1, loc1) and PUT(obj2, loc2)
```

To do this several things need to happen. First is that the tool needs to be updated to allow that, which may be tedious but not too hard. But the biggest problem may be that the format of the current JSON output does not really allow the above.

```json
{
	"identifier": "a0002",
	"name": "P0112",
	"start": 72000,
	"end": 81000,
	"predicate": "PUT",
	"arguments": {
		"Object": "LargeBlueBlock5",
		"Location": "in-front-of(FirstLayerAboveBase)" },
	"properties": {},
	"tier": "ACTION1",
	"task": "DPIP-Actions"
}
```

There is an ugly solution where you add predicate2 and arguments2, but I do not want to go there. To complicate matters, we have cases where a predicate name can be squeezed into the arguments:

```json
{
	"task": "Actions",
	"tier": "Actions",
	"identifier": "a0023",
	"name": "O0023",
	"start": 23000,
	"end": 45000,
	"predicate": "OTHER",
	"arguments": {
		"Predicate": "NewPredicate",
		"ARG0": "ARG0",
		"ARG1": "ARG1",
		"ARG2": null },
	"properties": {}
}
```

The above is not so much a problem for the syntax, but more an issue on whether there is a intuitive and general way to interpret the data. So I will ignore it for now and focus on thow to get in conjunctions (and disjunctions) while still supporting the above,that is, we will keep "predicate" and "arguments" around for backward compatibility in the sense that the tool can read it and put the data in the appropriate spot.


## New representation

We introduce a new property called "formula" (maybe later renamed into "logical_form" or "lf" or even "predicate") where the value can simply be a predicate-arguments object as above (where we bundle the predicate and arguments properties in one object). So the structure below replaces the predicate and arguments properties above for the simple case of a non-complex single predicate:

```json
{
	"formula": {
		"predicate": "PUT",
		"arguments": {
			"Object": "LargeBlueBlock5",
			"Location": "in-front-of(FirstLayerAboveBase)"
		}
	]
}
```

When introducing logical operators we employ some extra structure:

```json
{
	"formula": {
		"AND": [
			{
				"predicate": "PUT",
				"arguments": {
					"Object": "LargeBlueBlock5",
					"Location": "in-front-of(FirstLayerAboveBase)" }
			},
			{
				"predicate": "PUT",
				"arguments": {
					"Object": "SmallRedBlock3",
					"Location": "in-front-of(FirstLayerAboveBase)" }
			}
		]
	}
}
```

You could have negation in there:

```json
{
	"formula": {
		"AND": [
			{
				"NOT": {
					"predicate": "PUT",
					"arguments": {
						"Object": "LargeBlueBlock5",
						"Location": "in-front-of(FirstLayerAboveBase)" } }
			},
			{
				"predicate": "PUT",
				"arguments": {
					"Object": "SmallRedBlock3",
					"Location": "in-front-of(FirstLayerAboveBase)" }
			}
		]
	}
}
```

And this also allows arbitrary depth.

So basically we have:

```
Formula ==> { "predicate": DoubleQuotedString, "arguments": Dictionary }
Formula ==> { "NOT": Formula }
Formula ==> { "AND/OR": Formula+ }
Dictionary ==> { ArgName: ArgValue, ... }
ArgName ==> DoubleQuotedString 
ArgValue ==> DoubleQuotedString 
```


## Implementation plan

For the current purpose, we can start with a partial implementation which allows for just the predicate-arguments object and then add a simple conjunction.


### The new Predicate class

We will start here since it is just an addition and would be easy to test because all we do at first is include it when annotations are loaded from the JSON file. The name may be a bit confusing now but should not be once this change has been fully implemented. For now it just stores the name and the dictionary of argument, it also knows how to copy itself.

```python
class Predicate:

    def __init__(self, name: str, arguments: dict):
        self.name = name
        self.arguments = arguments

    def __str__(self):
        return f'<Predicate "{self.name}" with {len(self.arguments)} arguments>'

    def copy(self):
        return Predicate(self.name, deepcopy(self.arguments))
```

### Initial changes to the Annotation class

Replaced the "predicate" and "argument" instance variables with "_formula", which contains a Predicate instance. Added "predicate" and "arguments" properties for backward compatibility and to find them at their new place. These should probably be deprecated at some point.

The new properties reduced the number of changes needed, but still needed to fix methods that either create the JSON output, load annotations from disk or create and populate new annotations. This included copy(), as_json() and import_fields(). The latter was actually replaced with a class method from_dictionary().

Some methods did not need to be changed now, but will most likely need to be changed later, this includes as_formula() and maybe more.


### The new LogicalForm class

This is to make sure that we can deal with the LogicalForm grammar in the BNF above. The salient bits are repeated here:

```
Formula ==> { "predicate": DoubleQuotedString, "arguments": Dictionary }
Formula ==> { "NOT": Formula }
Formula ==> { "AND/OR": Formula+ }
```

We don't have to worry about Dictionary and DoubleQuotedString because Python has those, and the right-hand-side of the first line was already implemented in the Predicate class. All we need now is a class for the conjunction:

```python
class Conjunction:

	def __init__(self, predicates: list):
		self.conjuncts = predicates
```

We will most likely make Predicate and Conjunction subclasses of LogicalForm, which will probably be an abstract class.


### Add conjunctions to the Annotation class

TBD


### Add conjunctions to the Streamlit application

TBD

