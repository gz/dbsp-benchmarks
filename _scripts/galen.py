from utils import DATA_PATH, GALEN_BENCHMARKS, load_results_generic
import altair as alt
import pandas as pd


def load_galen_result(machine, revision, args):
    return load_results_generic(GALEN_BENCHMARKS / machine['name'] / revision / 'galen_results.csv.gz')


def load_galen_results(machine, args):
    "Loads galen results from CI runs."
    ci_result_file = DATA_PATH / "{}.csv".format(machine['name'])
    results = []
    if ci_result_file.exists():
        df = pd.read_csv(ci_result_file)
        for _idx, row in df.iterrows():
            galen_df = load_galen_result(machine, row['revision'], args)
            if galen_df is not None:
                galen_df['branches'] = row['branch']
                galen_df['date'] = row['date']
                galen_df['commit_msg'] = row['commit_msg']
                galen_df['git_rev'] = row['revision']
                results.append(galen_df)
            else:
                print("Can't determine commit info, skipping {}.".format(
                    row['revision']))
        try:
            nexmark_all = pd.concat(results).sort_values('date')
            nexmark_all['date'] = pd.to_datetime(
                nexmark_all['date'], utc=True)
            return nexmark_all
        except ValueError:
            return None
    else:
        print("Not found")
        return None


def galen_ci_graph(machine, args):
    "Generates a CI graph for galen"
    dataset = load_galen_results(machine, args)
    if dataset is None or dataset.empty:
        return None
    dataset.reset_index(inplace=True)

    # Make chart for GET Tput
    line = alt.Chart(dataset).mark_line(
        size=3
    ).transform_window(
        rolling_mean='mean(elapsed)',
        frame=[-5, 5],
    ).encode(
        x='date:T',
        y='rolling_mean:Q',
    )

    points = alt.Chart(dataset).mark_point().encode(
        x=alt.X('date:T', axis=alt.Axis(title='Commit Date')),
        y=alt.Y('elapsed:Q',
                axis=alt.Axis(title='Time [s]')),
        tooltip=["commit_msg:N", "date:T", "branches:N", "git_rev:N"],
    )
    chartGet = (line + points)
    chart = alt.vconcat(chartGet)

    chart.save(str(GALEN_BENCHMARKS / machine['name'] /
                   "galen_ci_graph.json"), format="json")
