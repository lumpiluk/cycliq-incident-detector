import sys
import math
import argparse
import json
import pathlib
import subprocess
import bpy


class ArgumentParserForBlender(argparse.ArgumentParser):
    """
    This class is identical to its superclass, except for the parse_args
    method (see docstring). It resolves the ambiguity generated when calling
    Blender from the CLI with a python script, and both Blender and the script
    have arguments. E.g., the following call will make Blender crash because
    it will try to process the script's -a and -b flags:
    >>> blender --python my_script.py -a 1 -b 2

    To bypass this issue this class uses the fact that Blender will ignore all
    arguments given after a double-dash ('--'). The approach is that all
    arguments before '--' go to Blender, arguments after go to the script.
    The following calls work fine:
    >>> blender --python my_script.py -- -a 1 -b 2
    >>> blender --python my_script.py --

    From https://blender.stackexchange.com/a/134596
    """

    def _get_argv_after_doubledash(self):
        """
        Given the sys.argv as a list of strings, this method returns the
        sublist right after the '--' element (if present, otherwise returns
        an empty list).
        """
        try:
            idx = sys.argv.index("--")
            return sys.argv[idx+1:] # the list after '--'
        except ValueError as e: # '--' not in the list:
            return []

    # overrides superclass
    def parse_args(self):
        """
        This method is expected to behave identically as in the superclass,
        except that the sys.argv list will be pre-processed using
        _get_argv_after_doubledash before. See the docstring of the class for
        usage examples and details.
        """
        return super().parse_args(args=self._get_argv_after_doubledash())


def blender_main():
    parser = ArgumentParserForBlender()
    parser.add_argument(
        "file",
        help="Name of the blend file to save",
    )
    parser.add_argument(
        '--incidents-json',
        type=pathlib.Path,
        required=True,
    )
    parser.add_argument(
        '--context-time',
        type=float,
        help="Seconds of context before and after a beep.",
        default=7,
    )
    args = parser.parse_args()

    bpy.context.preferences.view.show_splash = False
    bpy.ops.wm.read_homefile(app_template="Video_Editing")

    # `AttributeError: 'Screen' object has no attribute 'params':
    # bpy.data.screens["Video Editing"].params.directory = "//"

    with open(args.incidents_json, 'r') as f:
        incident_times_by_video = json.load(f)
    if len(incident_times_by_video) == 0:
        print("No incidents found")
        return

    # We'll assume that all videos have the same resolution and frame rate.
    # -> Set Blender settings accordingly:
    exif = get_exif(sorted(incident_times_by_video.keys())[0])
    bpy.context.scene.render.resolution_x = int(exif['Source Image Width'])
    bpy.context.scene.render.resolution_y = int(exif['Source Image Height'])
    fps = float(exif['Video Frame Rate'])
    bpy.context.scene.render.fps = math.ceil(fps)
    bpy.context.scene.render.fps_base = math.ceil(fps) / fps

    for video_filename in sorted(incident_times_by_video.keys()):
        for beep_time in incident_times_by_video[video_filename]:
            add_incident_to_timeline(
                video_filename=video_filename,
                beep_time=beep_time,
                context_time=args.context_time,
            )


def add_incident_to_timeline(
    video_filename: str,
    beep_time: float,
    context_time: float,
):
    bpy.context.scene.sequence_editor.sequences.new_movie(
        name=video_filename,
        filepath=video_filename,  # TODO: path?
        frame_start=0,  # TODO
        channel=0,
    )
    # if beep_time < context_time:
    #     # TODO: check if previous video file exists
    #     pass
    # video_len = 0  # TODO
    # if beep_time > video_len - context_time:
    #     # TODO: check if next video file exists
    #     pass


def get_exif(
    file_path: pathlib.Path,
):
    exiftool_process = subprocess.Popen(
        ['exiftool', str(file_path)],
        stdout=subprocess.PIPE,
    )
    metrics = dict()
    for line in exiftool_process.stdout:
        k, v = str(line).split(':', maxsplit=1)
        metrics[k.strip()[2:]] = v.strip()[:-3]
        # '[2:] is for removing the "b'" at the start
        # '[:-3] is for removing the trailing '\\n'
    return metrics


if __name__ == '__main__':
    blender_main()
