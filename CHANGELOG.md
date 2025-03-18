# Change Log

All notable changes to this project are documented in this file.

This project uses a simple versioning scheme with major and minor versions. Major versions are for significant updates with more than minimal functionality changes. Minor versions are for small functionality changes, documentation updates, small fixes and patches, and under-the-hood changes.


## Version 3.0 — 2025-03-17

- Replaced timeline slider with number inputs, which sped up the tool, made it more precise on large videos.
- Now using asynchronous calls to get frames from a video, which together with the change above greatly reduced any lock issues
- Lock issues now also seem to be caught in error handling code added for this version.
- Tidied up creation of ELAN output, is now done by clicking a button in the annotations view.
- Some general smoothing of the interface.

## Version 2.0 — 2025-02-26

- Added annotation tasks as the basic organizational layer.
- Streamlined configuration of tasks and tiers.
- Generalized blocks pool to an object pool. 
- Updated timeline display, adding a set of thumbnails for the first 5 seconds of a selected annotation.
- Streamlined the image cache.

## Version 1.0 — 2025-02-17

- First version where the tool is almost ready for full blast annotation, but extensive testing is still very much appreciated.
 