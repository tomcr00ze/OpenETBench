"""
OpenETBench
-----------

Monthly temporal harmonization for multi-year external ET products.
"""

from __future__ import annotations

import pandas as pd


def aggregate_observed_to_monthly(
    observed: pd.DataFrame,
    year: int,
    *,
    min_daily_coverage: float = 0.80,
) -> pd.DataFrame:
    """
    Aggregate daily BharatFlux ET to monthly totals.

    BharatFlux ET is in mm/day. Therefore the monthly benchmark quantity is
    the sum of valid daily ET observations.

    A month is retained only when the fraction of valid daily observations
    reaches ``min_daily_coverage``. Missing days are not imputed or scaled.
    """

    required = {"DoY", "ET"}
    missing = required.difference(observed.columns)
    if missing:
        raise KeyError(
            "Observed dataframe is missing required columns: "
            + ", ".join(sorted(missing))
        )

    data = observed.copy()
    data["DoY"] = pd.to_numeric(data["DoY"], errors="coerce")
    data["ET"] = pd.to_numeric(data["ET"], errors="coerce")
    data = data.dropna(subset=["DoY"]).copy()

    data["DoY"] = data["DoY"].astype(int)
    data["Date"] = (
        pd.Timestamp(year=year, month=1, day=1)
        + pd.to_timedelta(data["DoY"] - 1, unit="D")
    )
    data["Month"] = data["Date"].dt.month

    expected = (
        data.groupby("Month")["Date"]
        .nunique()
        .rename("observed_calendar_days")
    )

    # Use calendar month lengths, independent of whether the source file has
    # every day represented.
    month_lengths = pd.Series(
        {
            month: pd.Period(f"{year}-{month:02d}").days_in_month
            for month in range(1, 13)
        },
        name="expected_days",
    )

    valid = (
        data.dropna(subset=["ET"])
        .groupby("Month")["ET"]
        .agg(
            Observed_ET="sum",
            valid_days="count",
        )
    )

    out = month_lengths.to_frame()
    out = out.join(expected, how="left").join(valid, how="left")
    out["observed_calendar_days"] = out["observed_calendar_days"].fillna(0)
    out["valid_days"] = out["valid_days"].fillna(0)
    out["coverage"] = out["valid_days"] / out["expected_days"]

    out.loc[
        out["coverage"] < min_daily_coverage,
        "Observed_ET",
    ] = pd.NA

    out["Date"] = pd.to_datetime(
        [f"{year}-{month:02d}-01" for month in out.index]
    )
    out["Year"] = year
    out["Month"] = out.index.astype(int)

    return out.reset_index(drop=True)[
        [
            "Date",
            "Year",
            "Month",
            "Observed_ET",
            "valid_days",
            "expected_days",
            "coverage",
        ]
    ]


def merge_monthly_observed_product(
    observed_monthly: pd.DataFrame,
    product_monthly: pd.DataFrame,
) -> pd.DataFrame:
    """Merge monthly BharatFlux ET and external-product ET by year/month."""

    required_obs = {"Date", "Observed_ET"}
    required_product = {"Date", "ET"}

    missing_obs = required_obs.difference(observed_monthly.columns)
    missing_product = required_product.difference(product_monthly.columns)

    if missing_obs:
        raise KeyError(
            "Monthly observed dataframe is missing: "
            + ", ".join(sorted(missing_obs))
        )
    if missing_product:
        raise KeyError(
            "Monthly product dataframe is missing: "
            + ", ".join(sorted(missing_product))
        )

    obs = observed_monthly.copy()
    prod = product_monthly.copy()

    obs["Date"] = pd.to_datetime(obs["Date"]).dt.to_period("M").dt.to_timestamp()
    prod["Date"] = pd.to_datetime(prod["Date"]).dt.to_period("M").dt.to_timestamp()

    merged = obs.merge(
        prod[["Date", "ET"]].rename(columns={"ET": "Satellite_ET"}),
        on="Date",
        how="inner",
    )

    return merged.sort_values("Date").reset_index(drop=True)
