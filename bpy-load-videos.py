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
        '--context-before',
        type=float,
        help="Seconds of context before a beep.",
        default=14,
    )
    parser.add_argument(
        '--context-after',
        type=float,
        help="Seconds of context after a beep.",
        default=5,
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

    i_incident = 0
    for video_filename in sorted(incident_times_by_video.keys()):
        for beep_time in incident_times_by_video[video_filename]:
            print(f"Adding incident {video_filename=}, {beep_time=} s")
            add_incident_to_timeline(
                video_filename=video_filename,
                beep_time=beep_time,
                context_before=args.context_before,
                context_after=args.context_after,
                start_frame = int(
                    i_incident
                    * (args.context_before + args.context_after)
                    * fps
                ),
                fps=fps,
            )
            i_incident += 1

    bpy.context.scene.frame_end = int(
        i_incident
        * (args.context_before + args.context_after)
        * fps
    )

    # Update view in sequence editor
    # - Set frame range to include all strips
    # - Zoom out to show all
    # TODO: doesn't work

    # screen = bpy.data.screens['Video Editing']
    # print(f"{bpy.context.screen=}")
    # for area in screen.areas:
    #     if area.type == "SEQUENCE_EDITOR":
    #         override = bpy.context.copy()
    #         # change context to the sequencer
    #         override["screen"] = screen
    #         override["area"] = area
    #         override["region"] = area.regions[-1]
    #         # run the command with the correct context
    #         with bpy.context.temp_override(**override):
    #             bpy.ops.sequencer.set_range_to_strips()
    #             bpy.ops.sequencer.view_all()
    #         break


def add_incident_to_timeline(
    video_filename: str,
    beep_time: float,
    context_before: float,
    context_after: float,
    start_frame: int,
    fps: float,
):
    v_sequence = bpy.context.scene.sequence_editor.sequences.new_movie(
        name=video_filename,
        filepath=video_filename,  # TODO: path?
        frame_start=start_frame,
        channel=0,
    )
    a_sequence = bpy.context.scene.sequence_editor.sequences.new_sound(
        name=video_filename,
        filepath=video_filename,  # TODO: path?
        frame_start=start_frame,
        channel=0,
    )

    print(f"new {v_sequence=}")
    frame_start = start_frame - (beep_time - context_before) * fps
    frame_offset_start = (beep_time - context_before) * fps
    frame_final_duration = int((context_before + context_after) * fps)
    v_sequence.frame_start = frame_start
    v_sequence.frame_offset_start = frame_offset_start
    v_sequence.frame_final_duration = frame_final_duration
    a_sequence.frame_start = frame_start
    a_sequence.frame_offset_start = frame_offset_start
    a_sequence.frame_final_duration = frame_final_duration
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
    for line in exiftool_process.stdout.readlines():
        k, v = str(line).split(':', maxsplit=1)
        metrics[k.strip()[2:]] = v.strip()[:-3]
        # '[2:] is for removing the "b'" at the start
        # '[:-3] is for removing the trailing '\\n'
    return metrics


if __name__ == '__main__':
    blender_main()
