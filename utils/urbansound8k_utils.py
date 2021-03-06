import glob
import os

import librosa
import numpy as np
import pandas as pd
from tqdm import tqdm

from utils import data_utils


def read_csv(path):
    if not os.path.exists(path):
        raise FileNotFoundError("File `%s` not exists." % path)

    with open(path) as f:
        df = pd.read_csv(f)

    return df


def windows(data, window_size):
    start = 0
    while start < len(data):
        yield int(start), int(start + window_size)
        start += (window_size / 2)


def extract_features(parent_dir, sub_dirs, file_ext="*.wav", bands=60, frames=41):
    window_size = 512 * (frames - 1)  # frame_size = 512
    log_specgrams = []
    labels = []
    for sub_dir in sub_dirs:
        file_paths = glob.glob(os.path.join(parent_dir, sub_dir, file_ext))
        for file_path in tqdm(file_paths, desc='Extracting from `%s`' % sub_dir):
            sound_clip, s = librosa.load(file_path)
            file_name = os.path.basename(file_path)
            label = file_name.split('-')[1]
            for (start, end) in windows(sound_clip, window_size):
                if len(sound_clip[start:end]) == window_size:
                    signal = sound_clip[start:end]
                    melspec = librosa.feature.melspectrogram(signal, n_mels=bands)
                    logspec = librosa.amplitude_to_db(melspec)
                    logspec = logspec.T.flatten()[:, np.newaxis].T
                    log_specgrams.append(logspec)
                    labels.append(label)

    log_specgrams = np.asarray(log_specgrams).reshape(len(log_specgrams), bands, frames, 1)
    features = np.concatenate((log_specgrams, np.zeros(np.shape(log_specgrams))), axis=3)
    for i in range(len(features)):
        features[i, :, :, 1] = librosa.feature.delta(features[i, :, :, 0])

    return np.array(features), np.array(labels, dtype=np.int)


if __name__ == '__main__':
    _features, _labels = extract_features(
        parent_dir=r'E:\机器学习\数据集\音频\UrbanSound8K\audio',
        sub_dirs=['fold%d' % i for i in range(1, 11)],
        file_ext='*.wav',
        bands=60,
        frames=41)

    _pairs = [(f, l) for f, l in zip(_features, _labels)]
    data_utils.save_data(
        obj=np.array(_pairs, dtype=[('feature', np.ndarray), ('label', np.int)]),
        file_path='../data/urbansound8k/pairs')
