from utils import DATA_PATH, LDBC_BENCHMARKS, load_results_generic
import altair as alt
import pandas as pd


def load_ldbc_result(machine, revision, args):
    return load_results_generic(
        LDBC_BENCHMARKS / machine["name"] / revision / "ldbc_results.csv.gz"
    )


def load_ldbc_results(machine, args):
    "Loads ldbc results from CI runs."
    ci_result_file = DATA_PATH / "{}.csv".format(machine["name"])
    results = []
    if ci_result_file.exists():
        df = pd.read_csv(ci_result_file)
        for _idx, row in df.iterrows():
            ldbc_df = load_ldbc_result(machine, row["revision"], args)
            if ldbc_df is not None:
                ldbc_df["branches"] = row["branch"]
                ldbc_df["date"] = row["date"]
                ldbc_df["commit_msg"] = row["commit_msg"]
                ldbc_df["git_rev"] = row["revision"]
                results.append(ldbc_df)
                # print(results)
            else:
                print(
                    "Can't determine commit info, skipping {}.".format(row["revision"])
                )
        try:
            ldbc_all = pd.concat(results).sort_values("date")
            ldbc_all["date"] = pd.to_datetime(ldbc_all["date"], utc=True)
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
    dataset["kEVPS"] = dataset["evps"] / 1000

    # Make chart for GET Tput
    line = (
        alt.Chart(dataset)
        .mark_line(size=3)
        .transform_window(
            rolling_mean="mean(kEVPS)", frame=[-5, 5], groupby=["dataset"]
        )
        .encode(x="date:T", y="rolling_mean:Q", color="dataset:N")
    )

    points = (
        alt.Chart(dataset)
        .mark_point()
        .encode(
            x=alt.X("date:T", axis=alt.Axis(title="Commit Date")),
            y=alt.Y("kEVPS:Q", axis=alt.Axis(title="kEVPS")),
            tooltip=["commit_msg:N", "date:T", "branches:N", "git_rev:N"],
            color="dataset:N",
        )
    )
    chartGet = (line + points).facet("algorithm:N", columns=3)

    chart = alt.vconcat(chartGet)
    chart.save(
        str(LDBC_BENCHMARKS / machine["name"] / "ldbc_ci_graph.json"), format="json"
    )
