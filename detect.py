#!/usr/bin/env python3

# Helpful resource: https://apmonitor.com/dde/index.php/Main/AudioAnalysis

import io
import subprocess
import argparse
import pathlib
import json
import numpy as np
import matplotlib.pyplot as plt
import scipy.io
import scipy.signal


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--video-in',
        type=pathlib.Path,
        nargs='+',
    )
    parser.add_argument(
        '--json-out',
        type=pathlib.Path,
        required=True,
    )
    parser.add_argument(
        '--plot-volume',
        action='store_true',
    )
    parser.add_argument(
        '--plot-spectrogram',
        action='store_true',
    )
    args = parser.parse_args()

    triple_beeps_by_file = dict()
    for video_path in args.video_in:
        triple_beeps_by_file[str(video_path.name)] = process_video(
            video_path,
            plot_volume=args.plot_volume,
            plot_spectrogram=args.plot_spectrogram,
        )
    with open(args.json_out, 'w') as f:
        json.dump(triple_beeps_by_file, f, sort_keys=True, indent=2)


def process_video(
        video_path: pathlib.Path,
        plot_volume=False,
        plot_spectrogram=False,
):
    ffmpeg_process = subprocess.Popen(
        ['ffmpeg', '-i', video_path, '-f', 'wav', '-'],
        stdout=subprocess.PIPE,
    )
    audio_file = io.BytesIO(ffmpeg_process.stdout.read())

    sample_rate, samples = scipy.io.wavfile.read(audio_file)
    samples = samples[:, 0]  # use only one of the two stereo channels

    # downsample:
    target_rate = 8000
    resampling_ratio = target_rate / sample_rate
    a = scipy.signal.resample(samples, int(len(samples) * resampling_ratio))
    sample_rate = target_rate

    print('Sampling Rate:', sample_rate)
    print('Audio Shape:', np.shape(a))

    # xlim = (184, 186)  # known beep time in test.wav

    f_min = 2000
    f_max = 3000
    ex_times, ex_volume = extract_frequency(
        a,
        sample_rate,
        f_min=f_min,
        f_max=f_max
    )

    # find peaks
    peaks, props = scipy.signal.find_peaks(
        ex_volume,
        height=1000,
    )
    peak_times = ex_times[peaks]
    peak_vals = ex_volume[peaks]
    print(f"{peak_times=}\n{peak_vals=}\n{props=}")
    triple_beep_times = find_triple_beeps(
        peak_times,
        td_min=75e-3,
        td_max=100e-3
    )
    print(f"{triple_beep_times=}")

    if plot_volume:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(ex_times, ex_volume)
        # ax.set_xlim(*xlim)
        ax.set_xlim(130, 186)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Volume")
        ax.plot(peak_times, peak_vals, 'x')
        fig.savefig(f"{video_path.stem}_hz{f_min}-{f_max}.png")

    if plot_spectrogram:
        fig, ax = plt.subplots(figsize=(8, 6))
        freqs, times, spectrogram = scipy.signal.stft(a, fs=sample_rate)
        print(
            f"{np.shape(freqs)=}, {np.shape(times)=}, {np.shape(spectrogram)=}"
        )
        print(f"{len(freqs)=}, {len(times)=}")
        ax.pcolormesh(
            times,
            freqs,
            np.log(np.abs(spectrogram) + 1e-10),
            shading='gouraud',
            cmap='inferno'
        )
        ax.set_ylabel("Frequency (Hz)")
        ax.set_xlabel("time (s)")
        # ax.set_xlim(*xlim)
        fig.savefig(f"{video_path.stem}_spectrogram.png")

    return triple_beep_times


def find_triple_beeps(peak_times, td_min, td_max):
    peak_time_diffs = np.diff(peak_times)
    print(f"{peak_time_diffs=}")
    triple_beeps = []
    for i, peak_time_diff in enumerate(peak_time_diffs):
        if i == 0:
            continue
        if (
            td_min <= peak_time_diff <= td_max
            and td_min <= peak_time_diffs[i-1] <= td_max
        ):
            triple_beeps.append(peak_times[i])
    return triple_beeps


def extract_frequency(data, sample_rate: int, f_min=2000, f_max=3000):
    # With help from ChatGPT…
    freqs, times, spectrogram = scipy.signal.stft(data, fs=sample_rate)
    f_band_indices = np.where((freqs >= f_min) & (freqs <= f_max))[0]
    f_band = np.abs(spectrogram[f_band_indices])
    volume = np.sum(f_band, axis=0)
    return times, volume


if __name__ == '__main__':
    main()
