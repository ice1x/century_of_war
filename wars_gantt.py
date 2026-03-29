"""
wars_gantt.py
=============
Reads wars.csv and renders the Gantt timeline.
Called by app.py — do not run directly.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import CURRENT_YEAR, REGION_COLORS, REGION_KEYWORDS


def _guess_region(name: str) -> str:
    n = name.lower()
    for region, kws in REGION_KEYWORDS.items():
        if any(kw in n for kw in kws):
            return region
    return "Other"


@st.cache_data(show_spinner=False)
def load_data(csv_path: str = "wars.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["start_year", "end_year"])
    df["start_year"] = df["start_year"].astype(int)
    df["end_year"]   = df["end_year"].astype(int)
    df["duration"]   = df["end_year"] - df["start_year"]
    df["display_end"] = df["end_year"].where(df["duration"] > 0, df["start_year"] + 1)
    df["region"]     = df["name"].apply(_guess_region)
    df["wiki_url"]   = df.get("wiki_url", "").fillna("")
    df = df[(df["start_year"] >= 1900) & (df["start_year"] <= CURRENT_YEAR)]
    return df.sort_values(["start_year", "end_year"]).reset_index(drop=True)


def render(df: pd.DataFrame) -> None:

    # ── Sidebar ───────────────────────────────────────────────────────────────
    st.sidebar.markdown("## Filters")
    year_range       = st.sidebar.slider("Period", 1900, CURRENT_YEAR, (1900, CURRENT_YEAR))
    all_regions      = sorted(df["region"].unique())
    selected_regions = st.sidebar.multiselect("Regions", all_regions, default=all_regions)
    min_dur          = st.sidebar.slider("Min duration (years)", 0, 20, 0)
    search_query     = st.sidebar.text_input("Search by name")
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**Source:** [Wikipedia — List of wars]"
        "(https://en.wikipedia.org/wiki/List_of_wars:_1900%E2%80%931944)"
    )

    # ── Filter ────────────────────────────────────────────────────────────────
    mask = (
        (df["start_year"] <= year_range[1]) &
        (df["end_year"]   >= year_range[0]) &
        (df["region"].isin(selected_regions)) &
        (df["duration"]   >= min_dur)
    )
    if search_query:
        mask &= df["name"].str.contains(search_query, case=False, na=False)

    filtered = df[mask].copy()

    # Clip bar edges to selected window, ensure minimum visible width
    filtered["bar_start"] = filtered["start_year"].clip(lower=year_range[0])
    filtered["bar_end"]   = filtered["display_end"].clip(upper=year_range[1])
    filtered["bar_len"]   = (filtered["bar_end"] - filtered["bar_start"]).clip(lower=0.4)
    filtered = filtered.sort_values(["region", "start_year"]).reset_index(drop=True)

    # ── Metrics ───────────────────────────────────────────────────────────────
    total    = len(filtered)
    avg_dur  = round(filtered["duration"].mean(), 1) if total else 0
    most_reg = filtered["region"].value_counts().idxmax() if total else "—"
    longest  = filtered.loc[filtered["duration"].idxmax(), "name"] if total else "—"

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [
        (c1, total,          "Conflicts"),
        (c2, f"{avg_dur} yrs", "Avg. Duration"),
        (c3, most_reg,       "Top Region"),
        (c4, str(longest)[:28] + "..." if len(str(longest)) > 28 else longest, "Longest War"),
    ]:
        col.markdown(f"""
        <div class="metric-box">
            <div class="metric-val">{val}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if filtered.empty:
        st.warning("No conflicts match the selected filters.")
        return

    # ── Gantt figure ──────────────────────────────────────────────────────────
    #
    #   Horizontal bar:
    #       base = bar_start  → left edge  = start year
    #       x    = bar_len    → bar length = duration in years
    #   => right edge = base + x = start_year + duration = end_year  ✓
    #

    fig          = go.Figure()
    region_shown = set()

    for _, row in filtered.iterrows():
        color    = REGION_COLORS.get(row["region"], REGION_COLORS["Other"])
        show_leg = row["region"] not in region_shown
        region_shown.add(row["region"])

        dur_text = "< 1 year" if row["duration"] == 0 else f"{int(row['duration'])} years"
        hover = (
            f"<b>{row['name']}</b><br>"
            f"Region: {row['region']}<br>"
            f"Start:    {int(row['start_year'])}<br>"
            f"End:      {int(row['end_year'])}<br>"
            f"Duration: {dur_text}"
        )
        if row["wiki_url"]:
            hover += "<br><span style='color:#c8a882'>click to open Wikipedia ↗</span>"

        fig.add_trace(go.Bar(
            x            = [row["bar_len"]],    # LENGTH (years)
            y            = [row["name"]],
            base         = [row["bar_start"]],  # LEFT EDGE (start year)
            orientation  = "h",
            marker       = dict(color=color, opacity=0.82,
                                line=dict(color=color, width=0.5)),
            name         = row["region"],
            legendgroup  = row["region"],
            showlegend   = show_leg,
            hovertemplate= hover + "<extra></extra>",
            width        = 0.65,
            customdata   = [[row["wiki_url"], row["name"]]],
        ))

    for year, label in [(1914,"WWI begins"),(1918,"WWI ends"),
                        (1939,"WWII begins"),(1945,"WWII ends")]:
        if year_range[0] <= year <= year_range[1]:
            fig.add_vline(
                x=year,
                line=dict(color="rgba(255,255,200,0.20)", width=1, dash="dot"),
                annotation_text=label,
                annotation=dict(font=dict(color="rgba(255,255,200,0.45)", size=9),
                                textangle=-90, yanchor="bottom"),
            )

    chart_height = max(600, total * 20)

    fig.update_layout(
        barmode       = "overlay",
        height        = chart_height,
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
        font          = dict(family="Source Sans 3, sans-serif", color="#c8b898", size=11),
        xaxis         = dict(
            title         = "Year",
            range         = [year_range[0] - 0.5, year_range[1] + 0.5],
            tickmode      = "linear",
            dtick         = 10,
            gridcolor     = "rgba(200,170,130,0.08)",
            zerolinecolor = "rgba(0,0,0,0)",
            tickfont      = dict(color="#8a7a6a", size=10),
            title_font    = dict(color="#c8a882"),
        ),
        yaxis         = dict(
            autorange = "reversed",
            tickfont  = dict(size=9, color="#a09080"),
            gridcolor = "rgba(200,170,130,0.04)",
        ),
        legend        = dict(
            title       = dict(text="Region", font=dict(color="#c8a882")),
            bgcolor     = "rgba(15,10,8,0.85)",
            bordercolor = "rgba(200,168,130,0.2)",
            borderwidth = 1,
            font        = dict(color="#c8b898"),
            x=1.01, y=1,
        ),
        margin        = dict(l=240, r=160, t=30, b=60),
        hoverlabel    = dict(bgcolor="#1a120a", bordercolor="#c8a882",
                             font=dict(family="Source Sans 3", color="#e8d8b8")),
        clickmode     = "event",
    )

    import streamlit.components.v1 as components

    fig_json = fig.to_json()

    html = f"""
    <div id="gantt-chart"></div>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script>
        var fig = {fig_json};
        Plotly.newPlot('gantt-chart', fig.data, fig.layout, {{responsive: true}});

        document.getElementById('gantt-chart').on('plotly_click', function(data) {{
            var pt = data.points[0];
            if (pt && pt.customdata && pt.customdata[0]) {{
                window.open(pt.customdata[0], '_blank');
            }}
        }});

        // Make cursor pointer on hover over bars
        document.getElementById('gantt-chart').on('plotly_hover', function(data) {{
            var pt = data.points[0];
            if (pt && pt.customdata && pt.customdata[0]) {{
                document.getElementById('gantt-chart').style.cursor = 'pointer';
            }}
        }});
        document.getElementById('gantt-chart').on('plotly_unhover', function() {{
            document.getElementById('gantt-chart').style.cursor = 'default';
        }});
    </script>
    """
    components.html(html, height=chart_height + 60, scrolling=True)

    # ── Raw data table ────────────────────────────────────────────────────────
    with st.expander("Raw data"):
        disp = filtered[["name","start_year","end_year","duration","wiki_url"]].copy()
        disp.columns = ["Name","Start","End","Duration (yrs)","Wikipedia"]
        st.dataframe(disp, width="stretch", height=400)
        st.download_button(
            "Download CSV",
            data=disp.to_csv(index=False).encode("utf-8"),
            file_name="wars_filtered.csv",
            mime="text/csv",
        )

    # ── Conflicts per decade ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Conflicts per Decade")

    decade_df           = filtered.copy()
    decade_df["decade"] = (decade_df["start_year"] // 10) * 10
    all_decades         = sorted(decade_df["decade"].unique())
    decade_labels       = [str(d) + "s" for d in all_decades]

    decade_counts = (decade_df.groupby(["decade","region"])
                              .size().reset_index(name="count"))

    fig2 = go.Figure()
    for region in selected_regions:
        sub    = decade_counts[decade_counts["region"] == region].set_index("decade")
        y_vals = [int(sub.loc[d, "count"]) if d in sub.index else 0 for d in all_decades]
        fig2.add_trace(go.Bar(
            x=decade_labels, y=y_vals,
            name=region,
            marker_color=REGION_COLORS.get(region, "#8a8a8a"),
            opacity=0.85,
        ))

    fig2.update_layout(
        barmode="stack", height=340,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Source Sans 3", color="#c8b898"),
        xaxis=dict(
            gridcolor="rgba(200,170,130,0.07)",
            title_font=dict(color="#c8a882"),
            categoryorder="array",
            categoryarray=decade_labels,
        ),
        yaxis=dict(gridcolor="rgba(200,170,130,0.07)",
                   title="Number of conflicts",
                   title_font=dict(color="#c8a882")),
        legend=dict(bgcolor="rgba(15,10,8,0.8)",
                    bordercolor="rgba(200,168,130,0.2)", borderwidth=1),
        margin=dict(l=50, r=30, t=20, b=40),
    )
    st.plotly_chart(fig2, width="stretch")
