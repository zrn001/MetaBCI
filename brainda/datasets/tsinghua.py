# -*- coding: utf-8 -*-
#
# Authors: Swolf <swolfforever@gmail.com>
# Date: 2021/01/07
# License: MIT License
"""
Tsinghua BCI Lab.
"""
import os, zipfile
from typing import Union, Optional, Dict, List, Tuple
from pathlib import Path

import numpy as np
import py7zr
from mne import create_info
from mne.io import RawArray, Raw
from mne.channels import make_standard_montage
from .base import BaseDataset
from ..utils.download import mne_data_path
from ..utils.io import loadmat

# TSINGHUA_URL = 'http://bci.med.tsinghua.edu.cn/download.html'

Wang2016_URL = 'http://bci.med.tsinghua.edu.cn/upload/yijun/' #403 error, though it still works
# Wang2016_URL = "ftp://sccn.ucsd.edu/pub/ssvep_benchmark_dataset/"
# Wang2016_URL = 'http://www.thubci.com/uploads/down/' # This may work
BETA_URL = 'http://bci.med.tsinghua.edu.cn/upload/liubingchuan/' #403 error
# BETA_URL = 'https://figshare.com/articles/The_BETA_database/12264401'


class Wang2016(BaseDataset):
    """SSVEP dataset from Yijun Wang.

    This dataset gathered SSVEP-BCI recordings of 35 healthy subjects (17 females, aged 17-34 years, mean age: 22 years) focusing on 40 characters flickering at different frequencies (8-15.8 Hz with an interval of 0.2 Hz). For each subject, the experiment consisted of 6 blocks. Each block contained 40 trials corresponding to all 40 characters indicated in a random order. Each trial started with a visual cue (a red square) indicating a target stimulus. The cue appeared for 0.5 s on the screen. Subjects were asked to shift their gaze to the target as soon as possible within the cue duration. Following the cue offset, all stimuli started to flicker on the screen concurrently and lasted 5 s. After stimulus offset, the screen was blank for 0.5 s before the next trial began, which allowed the subjects to have short breaks between consecutive trials. Each trial lasted a total of 6 s. To facilitate visual fixation, a red triangle appeared below the flickering target during the stimulation period. In each block, subjects were asked to avoid eye blinks during the stimulation period. To avoid visual fatigue, there was a rest for several minutes between two consecutive blocks.

    EEG data were acquired using a Synamps2 system (Neuroscan, Inc.) with a sampling rate of 1000 Hz. The amplifier frequency passband ranged from 0.15 Hz to 200 Hz. Sixty-four channels covered the whole scalp of the subject and were aligned according to the international 10-20 system. The ground was placed on midway between Fz and FPz. The reference was located on the vertex. Electrode impedances were kept below 10 KΩ. To remove the common power-line noise, a notch filter at 50 Hz was applied in data recording. Event triggers generated by the computer to the amplifier and recorded on an event channel synchronized to the EEG data. 

    The continuous EEG data was segmented into 6 s epochs (500 ms pre-stimulus, 5.5 s post-stimulus onset). The epochs were subsequently downsampled to 250 Hz. Thus each trial consisted of 1500 time points. Finally, these data were stored as double-precision floating-point values in MATLAB and were named as subject indices (i.e., S01.mat, …, S35.mat). For each file, the data loaded in MATLAB generate a 4-D matrix named ‘data’ with dimensions of [64, 1500, 40, 6]. The four dimensions indicate ‘Electrode index’, ‘Time points’, ‘Target index’, and ‘Block index’. The electrode positions were saved in a ‘64-channels.loc’ file. Six trials were available for each SSVEP frequency. Frequency and phase values for the 40 target indices were saved in a ‘Freq_Phase.mat’ file.

    Information for all subjects was listed in a ‘Sub_info.txt’ file. For each subject, there are five factors including ‘Subject Index’, ‘Gender’, ‘Age’, ‘Handedness’, and ‘Group’. Subjects were divided into an ‘experienced’ group (eight subjects, S01-S08) and a ‘naive’ group (27 subjects, S09-S35) according to their experience in SSVEP-based BCIs.

    Frequency Table
    8    9   10   11   12   13   14   15
    8.2  9.2 10.2 11.2 12.2 13.2 14.2 15.2
    8.4  9.4 10.4 11.4 12.4 13.4 14.4 15.4
    8.6  9.6 10.6 11.6 12.6 13.6 14.6 15.6
    8.8  9.8 10.8 11.8 12.8 13.8 14.8 15.8

    Notes
    -----
    1. sub5 is not available from the download url.
    """
    _EVENTS = {str(i): (i, (0, 5)) for i in range(1, 41)}

    _CHANNELS = [
        'FP1', 'FPZ', 'FP2', 'AF3', 'AF4', 'F7', 'F5', 'F3', 'F1',
        'FZ', 'F2', 'F4', 'F6', 'F8', 'FT7', 'FC5', 'FC3', 'FC1',
        'FCZ', 'FC2', 'FC4', 'FC6', 'FT8', 'T7', 'C5', 'C3', 'C1',
        'CZ', 'C2', 'C4', 'C6', 'T8', 'TP7', 'CP5', 'CP3', 'CP1',
        'CPZ', 'CP2', 'CP4', 'CP6', 'TP8', 'P7', 'P5', 'P3', 'P1',
        'PZ', 'P2', 'P4', 'P6', 'P8', 'PO7', 'PO5', 'PO3', 'POZ',
        'PO4', 'PO6', 'PO8', 'O1', 'OZ', 'O2']

    _FREQS = np.arange(8, 16, 0.2).reshape((8, 5)).T.reshape((-1))
    _PHASES = np.arange(0, 0.5*40, 0.5).reshape((8, 5)).T.reshape((-1))%2
    
    def __init__(self):
        super().__init__(
            dataset_code='wang2016', 
            subjects=list(range(1, 36)),
            events=self._EVENTS, 
            channels=self._CHANNELS, 
            srate=250,
            paradigm='ssvep'
        )

    def data_path(self, 
            subject: Union[str, int], 
            path: Optional[Union[str, Path]] = None, 
            force_update: bool = False,
            update_path: Optional[bool] = None,
            proxies: Optional[Dict[str, str]] = None,
            verbose: Optional[Union[bool, str, int]] = None) -> List[List[Union[str, Path]]]:
        if subject not in self.subjects:
            raise(ValueError("Invalid subject id"))

        url = '{:s}S{:d}.mat.7z'.format(Wang2016_URL, subject)
        file_dest = mne_data_path(url, 'tsinghua', 
            path=path, proxies=proxies, force_update=force_update, update_path=update_path)
        
        if not os.path.exists(file_dest[:-3]):
            # decompression the data
            with py7zr.SevenZipFile(file_dest, 'r') as archive:
                archive.extractall(path=Path(file_dest).parent)
        dests = [
            [
                file_dest[:-3]
            ]
        ]
        return dests

    def _get_single_subject_data(self, subject: Union[str, int], 
            verbose: Optional[Union[bool, str, int]] = None) -> Dict[str, Dict[str, Raw]]:
        dests = self.data_path(subject)
        raw_mat = loadmat(dests[0][0])
        epoch_data = raw_mat['data'] * 1e-6
        stim = np.zeros((1, *epoch_data.shape[1:]))
        # insert event label at stimulus-onset
        # 0.5s latency
        stim[0, 125] = np.tile(np.arange(1, 41)[:, np.newaxis], (1, epoch_data.shape[-1]))
        epoch_data = np.concatenate((epoch_data, stim), axis=0)
        data = np.transpose(epoch_data, (0, 3, 2, 1))

        montage = make_standard_montage('standard_1005')
        montage.ch_names = [ch_name.upper() for ch_name in montage.ch_names]
        ch_names = [ch_name.upper() for ch_name in self._CHANNELS]
        ch_names.insert(32, 'M1')
        ch_names.insert(42, 'M2')
        ch_names.insert(59, 'CB1')
        ch_names = ch_names + ['CB2', 'STI 014']
        ch_types = ['eeg']*65
        ch_types[59] = 'misc'
        ch_types[63] = 'misc'
        ch_types[-1] = 'stim'

        info = create_info(
            ch_names=ch_names, ch_types=ch_types, sfreq=self.srate
        )

        runs = dict()
        for i in range(data.shape[1]):
            raw = RawArray(data=np.reshape(data[:, i, ...], (data.shape[0], -1)), info=info)
            raw.set_montage(montage)
            runs['run_{:d}'.format(i)] = raw

        sess = {
            'session_0': runs
        }
        return sess

    def get_freqs(self):
        return self._FREQS

    def get_phases(self):
        return self._PHASES


class BETA(BaseDataset):
    """BETA SSVEP dataset [1]_.

    EEG data after preprocessing are store as a 4-way tensor, with a dimension of channel x time point x block x condition. Each trial comprises 0.5-s data before the event onset and 0.5-s data after the time window of 2 s or 3 s. For S1-S15, the time window is 2 s and the trial length is 3 s, whereas for S16-S70 the time window is 3 s and the trial length is 4 s. Additional details about the channel and condition information can be found in the following supplementary information.

    Eight supplementary information is comprised of personal information, channel information, frequency and initial phase associated to each condition, SNR and sampling rate. The personal information contains age and gender of the subject. For the channel information, a location matrix (64 x 4) is provided, with the first column indicating channel index, the second column and third column indicating the degree and radius in polar coordinates, and the last column indicating channel name. The SNR information contains the mean narrow-band SNR and wide-band SNR matrix for each subject, calculated in (3) and (4), respectively. The initial phase is in radius.

    3-100Hz bandpass filtering (eegfilt), downsampled to 250 Hz

    References
    ----------
    .. [1] Liu B, Huang X, Wang Y, et al. BETA: A Large Benchmark Database Toward SSVEP-BCI Application[J]. Frontiers in neuroscience, 2020, 14: 627.
    """

    _EVENTS = {str(i): (i, (0, 2)) for i in range(1, 41)}

    _CHANNELS = [
        'FP1', 'FPZ', 'FP2', 'AF3', 'AF4', 'F7', 'F5', 'F3', 'F1',
        'FZ', 'F2', 'F4', 'F6', 'F8', 'FT7', 'FC5', 'FC3', 'FC1',
        'FCZ', 'FC2', 'FC4', 'FC6', 'FT8', 'T7', 'C5', 'C3', 'C1',
        'CZ', 'C2', 'C4', 'C6', 'T8', 'TP7', 'CP5', 'CP3', 'CP1',
        'CPZ', 'CP2', 'CP4', 'CP6', 'TP8', 'P7', 'P5', 'P3', 'P1',
        'PZ', 'P2', 'P4', 'P6', 'P8', 'PO7', 'PO5', 'PO3', 'POZ',
        'PO4', 'PO6', 'PO8', 'O1', 'OZ', 'O2']

    _FREQS = np.roll(np.arange(0, 0.2*40, 0.2)+8, -3)
    _PHASES = np.arange(0, 0.5*40, 0.5)%2
    
    def __init__(self):
        super().__init__(
            dataset_code='beta', 
            subjects=list(range(1, 71)),
            events=self._EVENTS, 
            channels=self._CHANNELS, 
            srate=250,
            paradigm='ssvep'
        )

    def data_path(self, 
            subject: Union[str, int], 
            path: Optional[Union[str, Path]] = None, 
            force_update: bool = False,
            update_path: Optional[bool] = None,
            proxies: Optional[Dict[str, str]] = None,
            verbose: Optional[Union[bool, str, int]] = None) -> List[List[Union[str, Path]]]:
        if subject not in self.subjects:
            raise(ValueError("Invalid subject id"))

        if subject < 11:
            url = '{:s}S1-S10.mat.zip'.format(BETA_URL)
        elif subject < 21:
            url = '{:s}S11-S20.mat.zip'.format(BETA_URL)
        elif subject < 31:
            url = '{:s}S21-S30.mat.zip'.format(BETA_URL)
        elif subject < 41:
            url = '{:s}S31-S40.mat.zip'.format(BETA_URL)
        elif subject < 51:
            url = '{:s}S41-S50.mat.zip'.format(BETA_URL)
        elif subject < 61:
            url = '{:s}S51-S60.mat.zip'.format(BETA_URL)
        else:
            url = '{:s}S61-S70.mat.zip'.format(BETA_URL)

        file_dest = mne_data_path(url, 'tsinghua', 
            path=path, proxies=proxies, force_update=force_update, update_path=update_path)

        parent_dir = Path(file_dest).parent
        
        if not os.path.exists(os.path.join(parent_dir, 'S{:d}.mat'.format(subject))):
            # decompression the data
            with zipfile.ZipFile(file_dest, 'r') as archive:
                archive.extractall(path=parent_dir)
        dests = [
            [
                os.path.join(parent_dir, 'S{:d}.mat'.format(subject))
            ]
        ]
        return dests

    def _get_single_subject_data(self, subject: Union[str, int], 
            verbose: Optional[Union[bool, str, int]] = None) -> Dict[str, Dict[str, Raw]]:
        dests = self.data_path(subject)
        raw_mat = loadmat(dests[0][0])
        epoch_data = raw_mat['data']['EEG'] * 1e-6
        stim = np.zeros((1, *epoch_data.shape[1:]))
        # 0.5s latency
        stim[0, 125] = np.tile(np.arange(1, 41), (epoch_data.shape[-2], 1))
        epoch_data = np.concatenate((epoch_data, stim), axis=0)
        data = np.transpose(epoch_data, (0, 3, 2, 1))

        montage = make_standard_montage('standard_1005')
        montage.ch_names = [ch_name.upper() for ch_name in montage.ch_names]
        ch_names = [ch_name.upper() for ch_name in self._CHANNELS]
        ch_names.insert(32, 'M1')
        ch_names.insert(42, 'M2')
        ch_names.insert(59, 'CB1')
        ch_names = ch_names + ['CB2', 'STI 014']
        ch_types = ['eeg']*65
        ch_types[59] = 'misc'
        ch_types[63] = 'misc'
        ch_types[-1] = 'stim'

        info = create_info(
            ch_names=ch_names, ch_types=ch_types, sfreq=self.srate
        )

        runs = dict()
        for i in range(data.shape[-2]):
            raw = RawArray(data=np.reshape(data[..., i, :], (data.shape[0], -1)), info=info)
            raw.set_montage(montage)
            runs['run_{:d}'.format(i)] = raw

        sess = {
            'session_0': runs
        }
        return sess

    def get_freqs(self):
        return self._FREQS

    def get_phases(self):
        return self._PHASES


