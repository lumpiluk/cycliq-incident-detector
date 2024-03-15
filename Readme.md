# Bicycle Dashcam Event Detector

Scrubbing through dashcam footage to find the actual incidents is tedious – especially if you live in a city where an incident happens every other kilometer.
This script listens to the triple-beep of Cycliq bicycle dashcams that you get when you press the record incident button.

## Usage

```bash
cd path/to/dashcam/footage

# Assuming this script is in your PATH
dashcam-detect.py --video-in ./*.MP4
```
