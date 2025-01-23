# DPIP Annotation Manual

This tool is for annotating actions in videos, more specifically, video of groups solving the DPIP task with large lego blocks.

## Installation

First get the Git repository with the annotation tool code:

```shell
git clone https://github.com/llc-trace/annotation-tool
```

To run the tool you need Python 3.10 or higher. To install needed dependencies do

```shell
pip install -r requirements.txt
```

See the README.md file in this repository for more details on installation. If you do not know what the above means then contact an annotation administrator for help.


## Running the tool

To run the tool do

```shell
streamlit run dpip_action_annotator.py PATH/VIDEO_FILE
```

When you first run the annotator on a new file, two empty data files and a log file are initialized in the `data/` directory: `VIDEO_FILE.json`, `VIDEO_FILE.tab` and `VIDEO_FILE.log`. The first data file has JSON representations of annotations as well as some other directives (like putting blocks in play or putting them back in the blocks pool) and the second data file contains lines that can be loaded into the Elan annotation tool. The log file collects all messages, at the moment there is not a lot in there.
