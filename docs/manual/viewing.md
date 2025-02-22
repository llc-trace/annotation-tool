# Timeline Annotator Manual

[ [home](index.md) 
| [configuration](configuration.md)
| [object pool](objects.md)
| [adding annotations](adding.md)
| [**viewing annotations**](viewing.md)
]

## Viewing Annotations

To view all annotations select the "show annotations" tool mode. 

<img src="images/view-annotations.png"/>

In this particular case the annotations file associated with the video has annotations from the four different tasks as described in the four configuration files bundled with the tool.

Clicking an item in the timeline generates a small representation of the seleced annotation immediately below the timeline.

> 🗒 You may wonder what the date under the timeline is doing there. The answer is that the widget used to display the annotations is a date-based timeline and there was no way to disable printing the date. The timeline widget was set up in such a way that the timeframe of the entire video starts at the first second of January 1st,

Entering a search term restricts the displayed annotations to just the ones that match the search term. The match is on normalized strings in the identifier, predicate, arguments and properties.

When clicking the "Hide controls" checkbox you will get access to functionality to delete annotations and reload annotations.