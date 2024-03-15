#!/usr/bin/env python3

# Helpful resource: https://apmonitor.com/dde/index.php/Main/AudioAnalysis

import sys
import io
import argparse
import pathlib
import numpy as np
import matplotlib.pyplot as plt
import scipy.io
import scipy.signal


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--audio-in',
        type=pathlib.Path,
    )
    args = parser.parse_args()
    audio_file = args.audio_in
    if not sys.stdin.isatty():
        # Using piped input instead,
        # and using BytesIO to avoid complaint that input is not seekable
        audio_file = io.BytesIO(sys.stdin.buffer.read())

    s, a = scipy.io.wavfile.read(audio_file)
    a = a[:, 0]  # use only one of the two stereo channels

    # downsample:
    target_rate = 8000
    resampling_ratio = target_rate / s
    a = scipy.signal.resample(a, int(len(a) * resampling_ratio))
    s = target_rate

    print('Sampling Rate:', s)
    print('Audio Shape:', np.shape(a))

    xlim = (184, 186)  # known beep time in test.wav

    # plot volume of frequency band
    fig, ax = plt.subplots(figsize=(8, 6))
    f_min = 2000
    f_max = 3000
    ex_times, ex_volume = extract_frequency(a, s, f_min=f_min, f_max=f_max)
    ax.plot(ex_times, ex_volume)
    ax.set_xlim(*xlim)
    # ax.set_xlim(130, 186)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Volume")

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

    ax.plot(peak_times, peak_vals, 'x')
    fig.savefig(f"test_hz{f_min}-{f_max}.png")

    # plot spectrogram
    fig, ax = plt.subplots(figsize=(8, 6))
    freqs, times, spectrogram = scipy.signal.stft(a, fs=s)
    print(f"{np.shape(freqs)=}, {np.shape(times)=}, {np.shape(spectrogram)=}")
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
    ax.set_xlim(*xlim)
    fig.savefig("test_spectrogram.png")


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
