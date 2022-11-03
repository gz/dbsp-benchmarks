from utils import DATA_PATH, NEXMARK_BENCHMARKS, load_results_generic
import altair as alt
import pandas as pd


def load_nexmark_result(machine, revision, args, file_name='nexmark_results.csv.gz'):
    return load_results_generic(NEXMARK_BENCHMARKS / machine['name'] / revision / file_name)


def load_nexmark_results(machine, args):
    "Loads nexmark results from CI runs."
    ci_result_file = DATA_PATH / "{}.csv".format(machine['name'])
    results = []
    if ci_result_file.exists():
        df = pd.read_csv(ci_result_file)
        for _idx, row in df.iterrows():
            nexmark_df = load_nexmark_result(machine, row['revision'], args)
            if nexmark_df is not None:
                nexmark_df['branches'] = row['branch']
                nexmark_df['date'] = row['date']
                nexmark_df['commit_msg'] = row['commit_msg']
                nexmark_df['git_rev'] = row['revision']
                results.append(nexmark_df)
                #print(results)
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


def nexmark_ci_graph(machine, args):
    "Generates a CI graph for nexmark"
    dataset = load_nexmark_results(machine, args)
    if dataset is None or dataset.empty:
        return None
    dataset.reset_index(inplace=True)
    dataset['tput'] = (dataset['num_events'] / dataset['elapsed']) / 1000
    dataset['name'] = dataset['name'].str.replace('q', '').astype(int)

    # Make chart for SET Tput
    line = alt.Chart(dataset).mark_line(
        size=3
    ).transform_window(
        rolling_mean='mean(tput)',
        frame=[-5, 5],
        groupby=['name']
    ).encode(
        x='date:T',
        y='rolling_mean:Q',
    )

    points = alt.Chart(dataset).mark_point().encode(
        x=alt.X('date:T', axis=alt.Axis(title='Commit Date')),
        y=alt.Y('tput:Q',
                axis=alt.Axis(title='Throughput [kOp/s]')),
        tooltip=["commit_msg:N", "date:T", "branches:N", "git_rev:N"],
    )
    # sort not working atm: https://github.com/vega/vega-lite/issues/5366
    # sort=['q0', 'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9', 'q12', 'q13', 'q14', 'q15', 'q16', 'q17', 'q18', 'q19', 'q20', 'q21', 'q22']
    chartSet = (line + points).facet('name:N', columns=3)

    chart = alt.vconcat(chartSet)
    chart.save(str(NEXMARK_BENCHMARKS / machine['name'] /
                   "nexmark_ci_graph.json"), format="json")
