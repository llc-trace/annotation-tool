# Timeline Annotator Manual

[ [home](index.md) 
| [**configuration**](configuration.md)
| [object pool](objects.md)
| [adding annotations](adding.md)
| [viewing annotations](viewing.md)
]

## Configuration

Configuration files contain annotation-specific settings. They can live anywhere but it is recommended that it is in the `config/` directory. Aside from the default configuration, the current repository has four configuration examples:

| configuration file     | description                          |
| ---------------------- | ------------------------------------ |
| config/gesture.py      | general gesture annotation           |
| config/gesture_dpip.py | gesture annotation for the DPIP task |
| config/action.py       | general action annotation            |
| config/action_dpip.py  | action annotation for the DPIP task  |


### The default configuration file

This file lives at `config/default.py` and has default settings for the tool. You should generally not be editing this file and instead edit the task-specific configuration files. It is worthwhile to read through this when creating your own configuration, purely for the comments. 

### Creating a configuration

🛠🧰🦺