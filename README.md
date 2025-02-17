# Annotation Tool

Tool for annotating actions and gestures.

To run this install Streamlit and OpenCV, ideally in a fresh virtual environment:

```shell
pip install streamlit
pip install streamlit-vis-timeline
pip install opencv-python
```

Or use the requirements file:

```shell
pip install -r requirements.txt
```

When using the requirements file you need at least Python 3.10. With individual pip-installs Python 3.9 has also been known to work.

To start the tool do

```shell
streamlit run dpip_action_annotator.py LOCAL_PATH/VIDEO_FILE.mp4 CONFIG_FILE
```

For the manual see [docs/manual/index.md](docs/manual/index.md).