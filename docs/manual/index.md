# Timeline Annotator Manual

[ [**home**](index.md) 
| [configuration](configuration.md)
| [object pool](objects.md)
| [adding annotations](adding.md)
| [viewing annotations](viewing.md)
]

## Introduction

The Timeline Annotator is meant for annotating actions and gestures in videos. Originally it was designed to work with videos of people solving Distributed Partial Information Puzzle (DPIP), a task involving building a structure of large lego blocks. While the tool has been somewhat generalized, there are still components of it that explicitly refer to lego blocks (for example the blocks pool), these can be ignored for other tasks.


### Installation

To install the tool get the Git repository with the annotation tool code:

```shell
git clone https://github.com/llc-trace/annotation-tool
```

To run the tool you need Python 3.10 or higher. To install needed dependencies do

```shell
pip install -r requirements.txt
```

The [README.md](../README.md) file in this repository has a few more details on installation. If you do not know what any of the above means then contact an annotation administrator for help.


### Starting the tool

To start the tool do

```shell
streamlit run annotator.py LOCAL_PATH/VIDEO_FILE.mp4 CONFIG_FILE [debug]
```

When you run this, a browser window should pop up automatically. If not, you can point your browser at [http://localhost:8501/](http://localhost:8501/).

When you first run the annotator on a new file, two empty data files and a log file are initialized in the `data/` directory: `VIDEO_FILE.json`, `VIDEO_FILE.tab` and `VIDEO_FILE.log`. The first data file has JSON representations of annotations as well as some other directives (like putting blocks in play or putting them back in the blocks pool) and the second data file contains lines that can be loaded into the Elan annotation tool. The log file collects all messages, at the moment there is not a lot in there and the log is rather sparse. 


### Next steps

The bundled configuration files may or may not work for you, if not you need to create your own annotation configuration, see the [configuration](configuration.md) instructions. Part of the configuration may be the definition of object pools. They are not necessary but can be handy for structuring and constraining the annotation process, see the [object pool](objects.md) page. 

You are now good to start annotating, see [adding annotations](adding.md) and [viewing annotations](viewing.md).