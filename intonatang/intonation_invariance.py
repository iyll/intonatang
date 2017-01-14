from __future__ import print_function, division

import os
results_path = os.path.join(os.path.dirname(__file__), 'results')

import numpy as np
import scipy.io as sio

from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

from tqdm import tqdm

from intonation_preanalysis import load_Y_mat_sns_sts_sps_for_subject_number

def test_invariance_control(subject_number, solver="lsqr", shrinkage=1, n_perms=1000):
    Y_mat, sns, sts, sps, Y_mat_plotter = load_Y_mat_sns_sts_sps_for_subject_number(subject_number)
    Y_mat_c, sns_c, sts_c, sps_c, Y_mat_plotter_c = load_Y_mat_sns_sts_sps_for_subject_number(subject_number, control_stim=True)

    Y_all = np.concatenate([Y_mat, Y_mat_c], axis=2)
    bad_time_indexes = np.isnan(np.sum(Y_all, axis=2))

    print(Y_mat.shape)
    n_chans, n_timepoints, n_trials = Y_mat.shape

    if solver == "svd":
        lda = LinearDiscriminantAnalysis()
    elif solver == "lsqr":
        lda = LinearDiscriminantAnalysis(solver=solver, shrinkage=shrinkage)

    accs = np.zeros((n_chans, n_perms, 3))
    accs_test = np.zeros((n_chans))

    n_train_100 = len(sts)
    n_test_100 = len(sts_c)
    n_train_80 = int(np.round(n_train_100*0.8))
    n_train_20 = n_train_100 - n_train_80

    ofs1 = sts
    ofs2 = sts_c

    for chan in np.arange(n_chans):
        Y_train = Y_mat[chan][~bad_time_indexes[chan]].T
        Y_test = Y_mat_c[chan][~bad_time_indexes[chan]].T

        if Y_train.shape[1] < 1 or Y_test.shape[1] < 1:
            accs_test[chan] = np.NaN
        else:
            lda.fit(Y_train, ofs1)
            accs_test[chan] = lda.score(Y_test, ofs2)

    for p in tqdm(np.arange(n_perms)):
        rand_perm_train = np.random.permutation(n_train_100)
        rand_perm_test = np.random.permutation(n_test_100)

        shuffle_train = np.random.permutation(n_train_100)
        shuffle_test = np.random.permutation(n_test_100)

        for chan in np.arange(n_chans):
            Y_train = Y_mat[chan][~bad_time_indexes[chan]].T
            Y_test = Y_mat_c[chan][~bad_time_indexes[chan]].T

            if Y_train.shape[1] < 1 or Y_test.shape[1] < 1:
                accs[chan, p, :] = np.NaN
            else:
                lda.fit(Y_train[rand_perm_train][np.arange(n_train_80)], ofs1[rand_perm_train][np.arange(n_train_80)])
                Y_speech_test = Y_train[rand_perm_train][np.arange(n_train_80, n_train_100)]
                Y_speech_shuffle = Y_train[shuffle_train][np.arange(n_train_80, n_train_100)]
                ofs1_test = ofs1[rand_perm_train][np.arange(n_train_80, n_train_100)]
                sample_inds = np.random.randint(0, Y_speech_test.shape[0], size=(n_test_100))
                Y_speech_test = Y_speech_test[sample_inds]
                Y_speech_shuffle = Y_speech_shuffle[sample_inds]
                ofs1_test = ofs1_test[sample_inds]

                accs[chan, p, 0] = lda.score(Y_speech_test, ofs1_test)
                accs[chan, p, 1] = lda.score(Y_speech_shuffle, ofs1_test)
                accs[chan, p, 2] = lda.score(Y_test[shuffle_test], ofs2)

    return accs, accs_test

def test_invariance_missing_f0(subject_number, solver="lsqr", shrinkage=1, n_perms=1000):
    Y_mat, sns, sts, sps, Y_mat_plotter = load_Y_mat_sns_sts_sps_for_subject_number(subject_number)
    Y_mat_c, sns_c, sts_c, sps_c, Y_mat_plotter_c = load_Y_mat_sns_sts_sps_for_subject_number(subject_number, missing_f0_stim=True)

    Y_all = np.concatenate([Y_mat, Y_mat_c], axis=2)
    bad_time_indexes = np.isnan(np.sum(Y_all, axis=2))

    print(Y_mat.shape)
    n_chans, n_timepoints, n_trials = Y_mat.shape

    if solver == "svd":
        lda = LinearDiscriminantAnalysis()
    elif solver == "lsqr":
        print('hi')
        lda = LinearDiscriminantAnalysis(solver=solver, shrinkage=shrinkage)

    accs = np.zeros((n_chans, n_perms, 4))
    accs_test = np.zeros((n_chans, 5))

    n_train_100 = len(sts)
    n_test_f0 = len(sns_c == 1) #2
    n_test_no_noise = len(sns_c == 0) #3
    n_test_stretch1 = len(sns_c == 2) #4
    n_test_stretchp5 = len(sns_c == 3) #5
    n_test_stretch2 = len(sns_c == 4) #6

    n_train_60 = int(np.round(n_train_100*0.6))
    n_train_40 = n_train_100 - n_train_60

    ofs_train = sts
    ofs0 = sts_c[sns_c == 0]
    ofs1 = sts_c[sns_c == 1]
    ofs2 = sts_c[sns_c == 2]
    ofs3 = sts_c[sns_c == 3]
    ofs4 = sts_c[sns_c == 4]
    ofs_tests = [ofs0, ofs1, ofs2, ofs3, ofs4]

    for chan in np.arange(n_chans):
        Y_train = Y_mat[chan][~bad_time_indexes[chan]].T

        for sn in np.arange(5):
            Y_test = Y_mat_c[chan][~bad_time_indexes[chan]].T[sns_c == sn]
            ofs_test = ofs_tests[sn]

            if Y_train.shape[1] < 1 or Y_test.shape[1] < 1:
                accs_test[chan, sn] = np.NaN
            else:
                lda.fit(Y_train, ofs_train)
                accs_test[chan, sn] = lda.score(Y_test, ofs_test)

    for p in tqdm(np.arange(n_perms)):
        rand_perm_train = np.random.permutation(n_train_100)
        shuffle_train = np.random.permutation(n_train_100)

        for chan in np.arange(n_chans):
            Y_train = Y_mat[chan][~bad_time_indexes[chan]].T

            if Y_train.shape[1] < 1 or Y_test.shape[1] < 1:
                accs[chan, p, :] = np.NaN
            else:
                lda.fit(Y_train[rand_perm_train][np.arange(n_train_60)], ofs_train[rand_perm_train][np.arange(n_train_60)])
                Y_speech_test = Y_train[rand_perm_train][np.arange(n_train_60, n_train_100)]
                Y_speech_shuffle = Y_train[shuffle_train][np.arange(n_train_60, n_train_100)]
                ofs_train_test = ofs_train[rand_perm_train][np.arange(n_train_60, n_train_100)]
                
                
                sample_inds48 = np.random.randint(0, Y_speech_test.shape[0], size=(48))
                sample_inds96 = np.random.randint(0, Y_speech_test.shape[0], size=(96))
                Y_speech_test48 = Y_speech_test[sample_inds48]
                Y_speech_shuffle48 = Y_speech_shuffle[sample_inds48]
                ofs_train_test48 = ofs_train_test[sample_inds48]

                Y_speech_test96 = Y_speech_test[sample_inds96]
                Y_speech_shuffle96 = Y_speech_shuffle[sample_inds96]
                ofs_train_test96 = ofs_train_test[sample_inds96]

                accs[chan, p, 0] = lda.score(Y_speech_test48, ofs_train_test48)
                accs[chan, p, 1] = lda.score(Y_speech_shuffle48, ofs_train_test48)
                accs[chan, p, 2] = lda.score(Y_speech_test96, ofs_train_test96)
                accs[chan, p, 3] = lda.score(Y_speech_shuffle96, ofs_train_test96)

    return accs, accs_test

def test_invariance(Y_mat, sns, sts, sps, of_what="st", to_what="sn", n_perms=1000, solver="svd", shrinkage=1):
    bad_time_indexes = np.isnan(np.sum(Y_mat, axis=2))
    Y_mat_orig = np.copy(Y_mat)
    condition_dict = {'st': sts, 'sn': sns, 'sp': sps}
    condition_labels = {'st':[1, 2, 3, 4], 'sn': [1,2,3,4], 'sp':[1,2,3]}

    ofs = condition_dict[of_what]
    tos = condition_dict[to_what]
    Y_resid = residualize(Y_mat, tos)
    n_chans, n_timepoints, n_trials = Y_mat.shape
    print(Y_mat.shape)

    if solver == "svd":
        lda = LinearDiscriminantAnalysis()
    elif solver == "lsqr":
        lda = LinearDiscriminantAnalysis(solver=solver, shrinkage=shrinkage)

    test_accs_distribution = False

    if test_accs_distribution:
        accs = np.zeros((n_chans, len(condition_labels[to_what]), n_perms, 8))
        for to_cond in tqdm(condition_labels[to_what]):
            n_train_100 = int(np.sum(tos != to_cond))
            n_test_100 = int(np.sum(tos == to_cond))
            n_test_50 = int(np.round(n_test_100/2))
            n1 = n_train_100 - n_test_50
            ofs1 = ofs[tos != to_cond]
            ofs2 = ofs[tos == to_cond]
            for p in tqdm(np.arange(n_perms)):
                rand_perm_train = np.random.permutation(n_train_100)
                rand_perm_test = np.random.permutation(n_test_100)

                shuffle_train = np.random.permutation(n_train_100)
                shuffle_test = np.random.permutation(n_test_100)

                for chan in np.arange(n_chans):
                    Y_mat_chan = Y_mat[chan][~bad_time_indexes[chan]]
                    Y_resid_chan = Y_resid[chan][~bad_time_indexes[chan]]

                    if Y_mat_chan.shape[0] < 1:
                        accs[chan, to_cond-1, p, :] = np.NaN
                    else:
                        Y_train = Y_mat_chan[:, tos != to_cond].T
                        Y_resid_train = Y_resid_chan[:, tos != to_cond].T
                        Y_test = Y_mat_chan[:, tos == to_cond].T
                        Y_resid_test = Y_resid_chan[:, tos == to_cond].T
                        
                        lda.fit(Y_train[rand_perm_train][np.arange(n1)], ofs1[rand_perm_train][np.arange(n1)])
                        accs[chan, to_cond-1, p, 0] = lda.score(Y_train[rand_perm_train][np.arange(n1, n_train_100)], ofs1[rand_perm_train][np.arange(n1, n_train_100)])
                        accs[chan, to_cond-1, p, 1] = lda.score(Y_test[rand_perm_test][np.arange(n_test_50)], ofs2[rand_perm_test][np.arange(n_test_50)])
                        accs[chan, to_cond-1, p, 2] = lda.score(Y_train[rand_perm_train][np.arange(n1, n_train_100)], ofs1[shuffle_train][np.arange(n1, n_train_100)])
                        accs[chan, to_cond-1, p, 3] = lda.score(Y_test[rand_perm_test][np.arange(n_test_50)], ofs2[shuffle_test][np.arange(n_test_50)])

                        lda.fit(Y_resid_train[rand_perm_train][np.arange(n1)], ofs1[rand_perm_train][np.arange(n1)])
                        accs[chan, to_cond-1, p, 4] = lda.score(Y_resid_train[rand_perm_train][np.arange(n1, n_train_100)], ofs1[rand_perm_train][np.arange(n1, n_train_100)])
                        accs[chan, to_cond-1, p, 5] = lda.score(Y_resid_test[rand_perm_test][np.arange(n_test_50)], ofs2[rand_perm_test][np.arange(n_test_50)])
                        accs[chan, to_cond-1, p, 6] = lda.score(Y_resid_train[rand_perm_train][np.arange(n1, n_train_100)], ofs1[shuffle_train][np.arange(n1, n_train_100)])
                        accs[chan, to_cond-1, p, 7] = lda.score(Y_resid_test[rand_perm_test][np.arange(n_test_50)], ofs2[shuffle_test][np.arange(n_test_50)])

    else:
        accs = np.zeros((n_chans, len(condition_labels[to_what]), n_perms, 8))
        for to_cond in tqdm(condition_labels[to_what]):
            n_train_100 = int(np.sum(tos != to_cond))
            n_test_100 = int(np.sum(tos == to_cond))
            n1 = n_train_100 - n_test_100
            ofs1 = ofs[tos != to_cond]
            ofs2 = ofs[tos == to_cond]

            for p in tqdm(np.arange(n_perms)):
                rand_perm_train = np.random.permutation(n_train_100)
                shuffle_train = np.random.permutation(n_train_100)
                shuffle_test = np.random.permutation(n_test_100)

                for chan in np.arange(n_chans):
                    Y_mat_chan = Y_mat[chan][~bad_time_indexes[chan]]
                    Y_resid_chan = Y_resid[chan][~bad_time_indexes[chan]]

                    if Y_mat_chan.shape[0] < 1:
                        accs[chan, to_cond-1, p, :] = np.NaN
                    else:
                        Y_train = Y_mat_chan[:, tos != to_cond].T
                        Y_resid_train = Y_resid_chan[:, tos != to_cond].T
                        Y_test = Y_mat_chan[:, tos == to_cond].T
                        Y_resid_test = Y_resid_chan[:, tos == to_cond].T

                        lda.fit(Y_train[rand_perm_train][np.arange(n1)], ofs1[rand_perm_train][np.arange(n1)])
                        accs[chan, to_cond-1, p, 0] = lda.score(Y_train[rand_perm_train][np.arange(n1, n_train_100)], ofs1[rand_perm_train][np.arange(n1, n_train_100)])
                        accs[chan, to_cond-1, p, 1] = lda.score(Y_test, ofs2) if p == 0 else np.NaN
                        accs[chan, to_cond-1, p, 2] = lda.score(Y_train[rand_perm_train][np.arange(n1, n_train_100)], ofs1[shuffle_train][np.arange(n1, n_train_100)])
                        accs[chan, to_cond-1, p, 3] = lda.score(Y_test, ofs2[shuffle_test])

                        lda.fit(Y_resid_train[rand_perm_train][np.arange(n1)], ofs1[rand_perm_train][np.arange(n1)])
                        accs[chan, to_cond-1, p, 4] = lda.score(Y_resid_train[rand_perm_train][np.arange(n1, n_train_100)], ofs1[rand_perm_train][np.arange(n1, n_train_100)])
                        accs[chan, to_cond-1, p, 5] = lda.score(Y_resid_test, ofs2) if p == 0 else np.NaN
                        accs[chan, to_cond-1, p, 6] = lda.score(Y_resid_train[rand_perm_train][np.arange(n1, n_train_100)], ofs1[shuffle_train][np.arange(n1, n_train_100)])
                        accs[chan, to_cond-1, p, 7] = lda.score(Y_resid_test, ofs2[shuffle_test])

    return accs

def save_invariance_test_accs(subject_number, accs, test_accs_distribution=False, of_what="st", to_what="sn", diagonal=False):
    info_str = ""
    if test_accs_distribution == False:
        info_str = info_str + "_single"
    if diagonal:
        info_str = info_str + "_diagonal"
    filename = os.path.join(results_path, 'EC' + str(subject_number) + '_invariance_test_of_' + of_what + '_to_' + to_what + '_accs' + info_str + '.mat')
    sio.savemat(filename, {'accs': accs})

def load_invariance_test_accs(subject_number, test_accs_distribution=False, of_what="st", to_what="sn", diagonal=False):
    info_str = ""
    if test_accs_distribution == False:
        info_str = info_str + "_single"
    if diagonal:
        info_str = info_str + "_diagonal"
    filename = os.path.join(results_path, 'EC' + str(subject_number) + '_invariance_test_of_' + of_what + '_to_' + to_what + '_accs' + info_str + '.mat')
    data = sio.loadmat(filename)
    return data['accs']

def save_control_test_accs(subject_number, accs, accs_test, diagonal=True):
    info_str = ""
    if diagonal:
        info_str = info_str + "_diagonal"
    filename = os.path.join(results_path, 'EC' + str(subject_number) + '_control_test_accs' + info_str + '.mat')
    sio.savemat(filename, {'accs': accs, 'accs_test': accs_test})

def load_control_test_accs(subject_number, diagonal=True):
    info_str = ""
    if diagonal:
        info_str = info_str + "_diagonal"
    filename = os.path.join(results_path, 'EC' + str(subject_number) + '_control_test_accs' + info_str + '.mat')
    data = sio.loadmat(filename)
    return data['accs'], data['accs_test']

def residualize(Y_mat, by):
    Y_resid = np.copy(Y_mat)
    for i, cond in enumerate(by):
        Y_resid[:,:,i] = Y_mat[:,:,i] - np.nanmean(Y_mat[:,:,by==cond], axis=2)
    return Y_resid