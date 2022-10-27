from utils import DATA_PATH, NEXMARK_BENCHMARKS, parse_git_info
import altair as alt
import pandas as pd


def load_nexmark_results(machine, args):
    "Loads nexmark results from CI runs."
    ci_result_file = DATA_PATH / "{}.csv".format(machine['name'])
    results = []
    if ci_result_file.exists():
        df = pd.read_csv(ci_result_file)
        for _idx, row in df.iterrows():
            results_csv_path = NEXMARK_BENCHMARKS / machine['name'] / \
                row['revision'] / 'nexmark_results.csv.gz'
            if results_csv_path.exists():
                nexmark_df = pd.read_csv(results_csv_path)
                print(nexmark_df)

                res = parse_git_info(row['revision'], args.repo)
                if res != None:
                    branches, commit_msg, commit_date = res
                    nexmark_df['branches'] = branches
                    nexmark_df['date'] = commit_date
                    nexmark_df['commit_msg'] = commit_msg
                    results.append(nexmark_df)
                    print(results)
                else:
                    print("Can't determine commit info, skipping.")
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
    dataset = load_nexmark_results(machine, args)
    "Generates a CI graph for nexmark"
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
    chart.save(str(NEXMARK_BENCHMARKS / machine['name'] /
                   "nexmark_ci_graph.json"), format="json")
