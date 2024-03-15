#!/usr/bin/env bash

ffmpeg -i "$0" -vn -f wav pipe:1 | ./detect.py
# TODO: we should be able to use subprocess in Python to call and pipe ffmpeg
