# Bicycle Dashcam Event Detector

Scrubbing through dashcam footage to find the actual incidents is tedious – especially if you live in a city where an incident happens every other kilometer.
This script listens to the triple-beep of Cycliq bicycle dashcams that you get when you press the record incident button.

After analyzing the footage, the script will output an `incidents.json` containing the detected incident timestamps.

If `--blender` is set, Blender will be opened and the video sequence editor (VSE) will be preloaded with the incidents plus a few seconds of context.

## Dependencies

- [Python](https://www.python.org/) (tested with 3.11)
  - [Scipy](https://scipy.org/)
- [FFmpeg](https://ffmpeg.org/)

Optional:
- [Blender](https://blender.org)
- [Exiftool](https://github.com/exiftool/exiftool)

## Usage

```bash
cd path/to/dashcam/footage

# Assuming this script is in your PATH
dashcam-detect.py --blender ./*.MP4
```
