from utils import DATA_PATH, LDBC_BENCHMARKS, load_results_generic
import altair as alt
import pandas as pd


def load_ldbc_result(machine, revision, args):
    return load_results_generic(LDBC_BENCHMARKS / machine['name'] / revision / 'ldbc_results.csv.gz')


def load_ldbc_results(machine, args):
    "Loads ldbc results from CI runs."
    ci_result_file = DATA_PATH / "{}.csv".format(machine['name'])
    results = []
    if ci_result_file.exists():
        df = pd.read_csv(ci_result_file)
        for _idx, row in df.iterrows():
            ldbc_df = load_ldbc_result(machine, row['revision'], args)
            if ldbc_df:
                results.append(ldbc_df)
                print(results)
            else:
                print("Can't determine commit info, skipping {}.".format(
                    row['revision']))
        try:
            ldbc_all = pd.concat(results).sort_values('date')
            ldbc_all['date'] = pd.to_datetime(
                ldbc_all['date'], utc=True)
            return ldbc_all
        except ValueError:
            return None
    else:
        print("Not found")
        return None


def ldbc_ci_graph(machine, args):
    dataset = load_ldbc_results(machine, args)
    "Generates a CI graph for ldbc"
    if dataset is None or dataset.empty:
        return None
    dataset.reset_index(inplace=True)

    # Make chart for GET Tput
    line = alt.Chart(dataset).mark_line(
        size=3
    ).transform_window(
        rolling_mean='mean(get)',
        frame=[-5, 5],
        groupby=['driver']
    ).encode(
        x='date:T',
        y='rolling_mean:Q',
        color='driver',
    )

    points = alt.Chart(dataset).mark_point().encode(
        x=alt.X('date:T', axis=alt.Axis(title='Commit Date')),
        y=alt.Y('get_total:Q',
                axis=alt.Axis(title='Throughput [Op/s]')),
        tooltip=["commit_msg:N", "date:T", "branches:N", "git_rev:N"],
        color='driver',
    )
    chartGet = (line + points).facet('cores:N', columns=3)

    # Make chart for SET Tput
    line = alt.Chart(dataset).mark_line(
        size=3
    ).transform_window(
        rolling_mean='mean(set)',
        frame=[-5, 5],
        groupby=['driver']
    ).encode(
        x='date:T',
        y='rolling_mean:Q',
        color='driver'
    )

    points = alt.Chart(dataset).mark_point().encode(
        x=alt.X('date:T', axis=alt.Axis(title='Commit Date')),
        y=alt.Y('set_total:Q',
                axis=alt.Axis(title='SET Throughput [Op/s]')),
        tooltip=["commit_msg:N", "date:T", "branches:N", "git_rev:N"],
        color='driver',
    )
    chartSet = (line + points).facet('cores:N', columns=3)

    chart = alt.vconcat(chartGet, chartSet)
    chart.save(str(LDBC_BENCHMARKS / machine['name'] /
                   "ldbc_ci_graph.json"), format="json")
