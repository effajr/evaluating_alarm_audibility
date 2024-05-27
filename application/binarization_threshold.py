"""
Computes F1-score, Precision and Recall for the trained models for evaluation label binarization thresholds varying
between 0.5 and 1. (See Sec.5.1, Fig.6 in the paper).

"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from predicting_alarm_audibility.scheme import *
import warnings
warnings.filterwarnings("ignore")


def main(config):

    # Make DataLoaders
    model, dev_dl, eval_dl = make()
    # Define evaluation annotators
    pool_a = get_annotator_pool(dev_dl, eval_dl, data_type='eval', pool_id='pool_a')
    pool_a_indices = get_annotator_indices(eval_dl, pool_a, data_type='eval')
    # Get non-binarized APF values
    apf = np.mean(eval_dl.dataset.y[:, pool_a_indices[0]], axis=1)

    # Compute model m_performance
    m_performance = pd.DataFrame()
    directory = f"trained_models/{config['folder']}"
    # Loop over models
    for k in range(10):
        model_name = f'run_{k+1}'
        model_ = load_weights(model, directory, model_name)
        _, output_ = inference(model_, eval_dl)

        # Compute evaluation metrics
        f1 = np.empty(len(config['thresholds']))
        precision = np.empty(len(config['thresholds']))
        recall = np.empty(len(config['thresholds']))
        for kk in range(len(config['thresholds'])):
            threshold = config['thresholds'][kk]
            f1_ = 100 * metrics.f1_score((apf > threshold).astype(int), np.round(output_))
            precision_ = 100 * metrics.precision_score((apf > threshold).astype(int), np.round(output_))
            recall_ = 100 * metrics.recall_score((apf > threshold).astype(int), np.round(output_))
            f1[kk], precision[kk], recall[kk] = f1_, precision_, recall_

        # Save model results
        performance_ = pd.DataFrame()
        run = np.tile(model_name, len(config['thresholds']))
        performance_['run'], performance_['threshold'], = run, config['thresholds']
        performance_['f1'], performance_['precision'], performance_['recall'] = f1, precision, recall
        m_performance = pd.concat([m_performance, performance_])

    # Compute human m_performance
    h_performance = pd.DataFrame()
    for k in range(len(config['thresholds'])):
        f1_ = human_performance(csv_path='./data/annotations/eval/eval_labels_apf.csv',
                                data_type='eval',
                                annotator_indices=pool_a_indices[0],
                                strategy='apf',
                                metric='f1',
                                bin_threshold=config['thresholds'][k])
        precision_ = human_performance(csv_path='./data/annotations/eval/eval_labels_apf.csv',
                                       data_type='eval',
                                       annotator_indices=pool_a_indices[0],
                                       strategy='apf',
                                       metric='precision',
                                       bin_threshold=config['thresholds'][k])
        recall_ = human_performance(csv_path='./data/annotations/eval/eval_labels_apf.csv',
                                    data_type='eval',
                                    annotator_indices=pool_a_indices[0],
                                    strategy='apf',
                                    metric='recall',
                                    bin_threshold=config['thresholds'][k])

        hperf_ = pd.DataFrame()
        hperf_['annotator'], hperf_['threshold'] = pool_a, np.tile(config['thresholds'][k], len(pool_a))
        hperf_['f1'], hperf_['precision'], hperf_['recall'] = f1_, precision_, recall_
        h_performance = pd.concat([h_performance, hperf_])

    # Display performance
    display_performance(m_performance, h_performance)

    return m_performance, h_performance


def display_performance(m_df, h_df):

    plt.figure('F1 score')
    sns.lineplot(data=m_df, x='threshold', y='f1', color='k', errorbar='se')
    sns.lineplot(data=h_df, x='threshold', y='f1', linestyle='--', color='k', errorbar='se')
    plt.xlim([0.5, 1])
    plt.ylim([0, 100])

    plt.figure('Precision')
    sns.lineplot(data=m_df, x='threshold', y='precision', color='cornflowerblue', errorbar='se')
    sns.lineplot(data=h_df, x='threshold', y='precision',
                 linestyle='--', color='cornflowerblue', errorbar='se')
    plt.xlim([0.5, 1])
    plt.ylim([0, 100])

    plt.figure('Rappel')
    sns.lineplot(data=m_df, x='threshold', y='recall', color='indianred', errorbar='se')
    sns.lineplot(data=h_df, x='threshold', y='recall', linestyle='--', color='indianred', errorbar='se')
    plt.xlim([0.5, 1])
    plt.ylim([0, 100])

    plt.show()

    return


def make():
    dev_ds_path = './features/dev/mel-spectrogram.h5'
    indices_csv_path = './data/annotations/dev/dev_train_valid_split.csv'
    dev_ds = Dataset(dev_ds_path, dev=True, split_indices_csv_path=indices_csv_path)
    dev_dl = DevDataLoader(dev_ds, 16)

    eval_ds_path = './features/eval/mel-spectrogram.h5'
    eval_ds = Dataset(eval_ds_path, dev=False, label_type='apf')
    eval_dl = EvalDataLoader(eval_ds, 16, training_mean=dev_dl.mean, training_std=dev_dl.std)

    model = CNN(in_channels=1)

    return model, dev_dl, eval_dl


if __name__ == '__main__':

    # Config
    parameters = {'folder': 'paper',
                  'thresholds': np.linspace(0.5, 1., 110)}

    # Compute metrics
    dfm, dfh = main(parameters)
