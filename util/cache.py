

class ImageCache:

    """Cache all images retrieved from the video. The images are indexed on the
    offset in milliseconds in the video. Values are what is returned by the method
    cv2.VideoCapture().read(), which is a Numpy array."""

    def __init__(self):
        self.data = {}

    def __len__(self):
        return len(self.data)

    def __str__(self):
        points = '{' + ' '.join([str(ms) for ms in self.data.keys()]) + '}'
        return f'<ImageCache with {len(self)} timepoints  {points}>'

    def __getitem__(self, i):
        return self.data[i]

    def __setitem__(self, i, val):
        self.data[i] = val

    def __contains__(self, item):
        return item in self.data

    def reset(self):
        self.data = {}
