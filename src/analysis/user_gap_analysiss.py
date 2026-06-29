import pandas as pd

RAW_PATH = (
    "datas/raw/raw.parquet"
)


def main():

    raw = pd.read_parquet(
        RAW_PATH
    )

    raw["timestamp"] = pd.to_datetime(
        raw["timestamp"]
    )

    df = raw.sort_values(
        [
            "user_id",
            "timestamp"
        ]
    )

    df["gap_seconds"] = (
        df.groupby("user_id")["timestamp"]
          .diff()
          .dt.total_seconds()
    )

    print("\n")
    print("=" * 80)
    print("USER GAP ANALYSIS")
    print("=" * 80)

    print(
        df["gap_seconds"]
        .describe()
    )

    print("\n")
    print("=" * 80)
    print("MOST COMMON GAPS")
    print("=" * 80)

    print(
        df["gap_seconds"]
        .round()
        .value_counts()
        .sort_index()
        .head(50)
    )

    print("\n")
    print("=" * 80)
    print("SMALL GAPS (< 60s)")
    print("=" * 80)

    small_gaps = df[
        df["gap_seconds"] <= 60
    ]

    print(
        f"Rows: {len(small_gaps):,}"
    )

    if len(small_gaps) > 0:

        print(
            small_gaps[
                [
                    "user_id",
                    "timestamp",
                    "gap_seconds"
                ]
            ]
            .head(50)
            .to_string(index=False)
        )

    print("\n")
    print("=" * 80)
    print("GAP BUCKETS")
    print("=" * 80)

    print(
        pd.cut(
            df["gap_seconds"],
            bins=[
                0,
                60,
                300,
                1800,
                3600,
                21600,
                86400,
                float("inf")
            ]
        )
        .value_counts()
        .sort_index()
    )

    print("\n")
    print("=" * 80)
    print("USERS WITH MOST SUB-60s TRANSACTIONS")
    print("=" * 80)

    sub60 = (
        df[
            df["gap_seconds"] <= 60
        ]
        .groupby("user_id")
        .size()
        .sort_values(
            ascending=False
        )
        .head(20)
    )

    print(sub60)

    print("\n")
    print("=" * 80)
    print("MAX VELOCITY USERS")
    print("=" * 80)

    max_gap_users = (
        df.groupby("user_id")
          ["gap_seconds"]
          .min()
          .sort_values()
          .head(20)
    )

    print(max_gap_users)


if __name__ == "__main__":
    main()