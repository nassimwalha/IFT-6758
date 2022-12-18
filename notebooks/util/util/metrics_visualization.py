from sklearn import metrics
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import percentileofscore
from sklearn.calibration import CalibrationDisplay


def generate_four_curves(model_name, ground_truth, prediction_probabilities, calibration_bins):
    sns.set_style("darkgrid")
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(16, 12))
    fpr, tpr, _ = metrics.roc_curve(ground_truth, prediction_probabilities)
    auc = metrics.roc_auc_score(ground_truth, prediction_probabilities)
    axes[0, 0].plot(fpr, tpr, label="data, auc=" + str(auc))
    axes[0, 0].plot([0, 1], [0, 1], color='orange', linestyle='--')
    axes[0, 0].set_xlabel('False Positive Rate')
    axes[0, 0].set_ylabel('True Positive Rate')
    axes[0, 0].set_title('Reciever Operating Characteristic (ROC) Curve')
    axes[0, 0].legend(loc=4)
    fig.suptitle(model_name, fontsize=20)
    Dict_proba = {'Goal_Proba': prediction_probabilities}
    df_proba = pd.DataFrame(Dict_proba)

    df_proba['Percentiles'] = df_proba.apply(lambda x: percentileofscore(df_proba['Goal_Proba'], x))

    df_proba['Goals'] = ground_truth
    df_proba_sorted = df_proba.sort_values(by='Percentiles', ascending=False)

    df_proba_sorted['Goals_Cum'] = df_proba_sorted['Goals'].cumsum()

    df_proba_sorted.reset_index(drop=True, inplace=True)
    df_proba_sorted['Event_count_cum'] = df_proba_sorted.index + 1

    df_proba_sorted = df_proba_sorted.assign(Goals_rate=lambda x: x['Goals_Cum'] / x['Event_count_cum'])

    df_proba_sorted['Goals_Cum_Portion'] = df_proba_sorted['Goals_Cum'] / max(df_proba_sorted['Goals_Cum'])

    sns.lineplot(df_proba_sorted, x='Percentiles', y='Goals_rate', ax=axes[0, 1])
    axes[0, 1].set_title("Goal rate")

    sns.lineplot(df_proba_sorted, x='Percentiles', y='Goals_Cum_Portion', ax=axes[1, 0])
    axes[1, 0].set_title("Cumulative % of goals")

    disp_test = CalibrationDisplay.from_predictions(ground_truth, prediction_probabilities, n_bins = calibration_bins)
    disp_test.plot(ax=axes[1, 1])
    axes[1, 1].set_title("Calibration curve")

    return fig