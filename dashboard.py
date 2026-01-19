#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anti-Bot Benchmark Dashboard

Streamlit dashboard for visualizing anti-bot scraper benchmark results.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(
    page_title="Anti-Bot Benchmark Dashboard",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Anti-Bot Benchmark Dashboard")
st.markdown("Visualize and analyze anti-bot scraper effectiveness across multiple websites")


def load_results(results_dir: str = "benchmark_results") -> List[Dict]:
    """Load all benchmark results from JSON files."""
    results_dir = Path(results_dir)
    all_results = []

    for filepath in results_dir.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_results.extend(data)
        except Exception as e:
            st.warning(f"Failed to load {filepath}: {e}")

    return all_results


def create_summary_cards(df: pd.DataFrame):
    """Create summary metric cards."""
    total = len(df)
    success = len(df[df["success"] == True])
    detected = len(df[df["detected_by_bot_protection"] == True])
    captcha = len(df[df["captcha_present"] == True])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Tests", total)

    with col2:
        success_rate = (success / total * 100) if total > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")

    with col3:
        detection_rate = (detected / total * 100) if total > 0 else 0
        st.metric("Detection Rate", f"{detection_rate:.1f}%")

    with col4:
        captcha_rate = (captcha / total * 100) if total > 0 else 0
        st.metric("Captcha Rate", f"{captcha_rate:.1f}%")


def create_success_by_domain_chart(df: pd.DataFrame):
    """Create success rate by domain chart."""
    domain_stats = df.groupby("domain").agg({
        "success": "mean",
        "detected_by_bot_protection": "mean",
    }).reset_index()
    domain_stats["success_rate"] = (domain_stats["success"] * 100).round(1)
    domain_stats["detection_rate"] = (domain_stats["detected_by_bot_protection"] * 100).round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=domain_stats["domain"],
        y=domain_stats["success_rate"],
        name="Success Rate",
        marker_color="#2ecc71",
    ))
    fig.add_trace(go.Bar(
        x=domain_stats["domain"],
        y=domain_stats["detection_rate"],
        name="Detection Rate",
        marker_color="#e74c3c",
    ))

    fig.update_layout(
        title="Success vs Detection Rate by Domain",
        barmode="group",
        xaxis_title="Domain",
        yaxis_title="Rate (%)",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def create_challenge_type_chart(df: pd.DataFrame):
    """Create challenge type distribution chart."""
    challenge_df = df[df["challenge_type"].notna()]
    if challenge_df.empty:
        st.info("No challenges detected in the results.")
        return

    challenge_counts = challenge_df["challenge_type"].value_counts().reset_index()
    challenge_counts.columns = ["challenge_type", "count"]

    fig = px.pie(
        challenge_counts,
        values="count",
        names="challenge_type",
        title="Challenge Types Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )

    st.plotly_chart(fig, use_container_width=True)


def create_load_time_distribution(df: pd.DataFrame):
    """Create load time distribution chart."""
    fig = px.box(
        df,
        x="domain",
        y="load_time_ms",
        title="Page Load Time Distribution by Domain",
        color="success",
        color_discrete_map={True: "#2ecc71", False: "#e74c3c"},
    )
    fig.update_layout(
        xaxis_title="Domain",
        yaxis_title="Load Time (ms)",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def create_elements_loaded_chart(df: pd.DataFrame):
    """Create elements loaded comparison chart."""
    fig = px.box(
        df,
        x="domain",
        y="elements_loaded",
        title="Elements Loaded by Domain",
        color="success",
        color_discrete_map={True: "#2ecc71", False: "#e74c3c"},
    )
    fig.update_layout(
        xaxis_title="Domain",
        yaxis_title="Number of Elements",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def create_http_status_chart(df: pd.DataFrame):
    """Create HTTP status code distribution chart."""
    status_df = df[df["http_status"].notna()]
    if status_df.empty:
        st.info("No HTTP status data available.")
        return

    status_counts = status_df["http_status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]

    fig = px.bar(
        status_counts,
        x="status",
        y="count",
        title="HTTP Status Code Distribution",
        color="count",
        color_continuous_scale="Viridis",
    )
    fig.update_layout(
        xaxis_title="HTTP Status",
        yaxis_title="Count",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def create_timeline_chart(df: pd.DataFrame):
    """Create timeline of test results."""
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    fig = px.scatter(
        df,
        x="timestamp",
        y="domain",
        color="success",
        symbol="detected_by_bot_protection",
        title="Test Results Timeline",
        color_discrete_map={True: "#2ecc71", False: "#e74c3c"},
        hover_data=["challenge_type", "http_status", "load_time_ms"],
    )
    fig.update_layout(
        xaxis_title="Timestamp",
        yaxis_title="Domain",
        height=500,
        legend_title_text="Success / Detected",
    )

    st.plotly_chart(fig, use_container_width=True)


def create_comparison_chart(df: pd.DataFrame):
    """Create anti-bot vs regular comparison chart."""
    st.subheader("Anti-Bot vs Regular Scraping Comparison")

    if "use_anti_bot" not in df.columns:
        st.info("Comparison data not available. Run comparison tests to see this chart.")
        return

    comparison_df = df.groupby(["domain", "use_anti_bot"]).agg({
        "success": "mean",
        "detected_by_bot_protection": "mean",
    }).reset_index()

    comparison_pivot = comparison_df.pivot(
        index="domain",
        columns="use_anti_bot",
        values="success"
    ).reset_index()

    if len(comparison_pivot.columns) > 2:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=comparison_pivot["domain"],
            y=comparison_pivot.get(True, 0) * 100,
            name="Anti-Bot",
            marker_color="#2ecc71",
        ))
        fig.add_trace(go.Bar(
            x=comparison_pivot["domain"],
            y=comparison_pivot.get(False, 0) * 100,
            name="Regular",
            marker_color="#95a5a6",
        ))

        fig.update_layout(
            title="Success Rate: Anti-Bot vs Regular Scraping",
            barmode="group",
            xaxis_title="Domain",
            yaxis_title="Success Rate (%)",
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough comparison data available.")


def display_results_table(df: pd.DataFrame):
    """Display detailed results table."""
    st.subheader("Detailed Results")

    display_df = df[[
        "timestamp",
        "domain",
        "success",
        "detected_by_bot_protection",
        "challenge_type",
        "http_status",
        "load_time_ms",
        "elements_loaded",
        "js_executed",
        "notes"
    ]].copy()

    display_df["timestamp"] = pd.to_datetime(display_df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    display_df = display_df.rename(columns={
        "timestamp": "Time",
        "domain": "Domain",
        "success": "Success",
        "detected_by_bot_protection": "Detected",
        "challenge_type": "Challenge",
        "http_status": "Status",
        "load_time_ms": "Load Time (ms)",
        "elements_loaded": "Elements",
        "js_executed": "JS Exec",
        "notes": "Notes"
    })

    st.dataframe(display_df, use_container_width=True, height=400)


def main():
    results = load_results()

    if not results:
        st.warning("No benchmark results found. Run the benchmark tests first using:")
        st.code("python run_benchmark.py", language="bash")
        return

    df = pd.DataFrame(results)

    st.sidebar.title("Filters")
    
    domains = df["domain"].unique().tolist()
    selected_domains = st.sidebar.multiselect(
        "Select Domains",
        options=domains,
        default=domains,
    )

    success_filter = st.sidebar.radio(
        "Filter by Success",
        options=["All", "Success Only", "Failed Only"],
        index=0,
    )

    filtered_df = df[df["domain"].isin(selected_domains)]

    if success_filter == "Success Only":
        filtered_df = filtered_df[filtered_df["success"] == True]
    elif success_filter == "Failed Only":
        filtered_df = filtered_df[filtered_df["success"] == False]

    st.markdown("---")

    create_summary_cards(filtered_df)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        create_success_by_domain_chart(filtered_df)

    with col2:
        create_challenge_type_chart(filtered_df)

    st.markdown("---")

    create_load_time_distribution(filtered_df)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        create_elements_loaded_chart(filtered_df)

    with col2:
        create_http_status_chart(filtered_df)

    st.markdown("---")

    create_timeline_chart(filtered_df)

    st.markdown("---")

    create_comparison_chart(filtered_df)

    st.markdown("---")

    display_results_table(filtered_df)

    st.markdown("---")

    st.subheader("Export Results")
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
