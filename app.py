import io
from typing import List, Tuple

import altair as alt
import pandas as pd
import parse
import streamlit as st

import graphs
import ml


def file_uploader(prompt: str, ext: str= 'csv') -> io.StringIO:
    return st.sidebar.file_uploader(prompt, key=prompt, type=ext)


@st.cache
def read_csv(csv_file: io.StringIO) -> pd.DataFrame:
    try:
        df = pd.read_csv(csv_file, header=1)
    except ValueError:
        df = pd.DataFrame()
    return df


def chart(cht: alt.Chart) -> None:
    st.altair_chart(cht, use_container_width=True)


@st.cache
def parse_times(
    hrr_df: pd.DataFrame,
    ctrl_df: pd.DataFrame,
    devc_df: pd.DataFrame,
    out_txt: str,
) -> Tuple[float, float, float]:
    t_start = 0.0
    t_cur = 0.0
    t_end = 0.0

    for df in [hrr_df, devc_df, ctrl_df]:
        try:
            t_start = min(t_start, df.Time.min())
            t_cur = max(t_end, df.Time.max())
        except AttributeError:
            continue

    if out_txt:
        start = parse.search("Simulation Start Time (s) {:>f}\n", out_txt)
        end = parse.search("Simulation End Time (s) {:>f}\n", out_txt)
        t_start = float(start.fixed[0])
        t_end = float(end.fixed[0])

        timesteps = parse_timesteps(out_txt)
        t_cur = max(t_cur, timesteps.time.max())

    t_end = max(t_end, t_cur)
    return t_start, t_cur, t_end


@st.cache
def parse_timesteps(out_text: str) -> pd.DataFrame:
    steps = parse.findall(
        "Step Size: {size:>e} s, Total Time: {time:>f} s",
        out_text
    )
    return pd.DataFrame([i.named for i in steps])


def parse_devc_meta(out_text: str) -> pd.DataFrame:
    devices = parse.findall(
        "Coords: {x:>f} {y:>f} {z:>f}, Make: {make}, ID: {id}, Quantity: {qty}\n",
        out_text
    )
    df = pd.DataFrame([i.named for i in devices])

    if df.empty or len(df.z.unique()) == 1:
        return df

    k = st.sidebar.slider(
        label='Number of Elevations',
        min_value=1,
        max_value=len(df.z.unique()),
        value=ml.best_k(df),
        step=1,
    )
    if k == 1:
        return df

    levels = ml.get_levels(df[['z']], k)
    df = df.merge(levels, on='z')

    return df


@st.cache
def get_activation_times(ctrl_df: pd.DataFrame) -> pd.DataFrame:
    changes = (
        ctrl_df.set_index('Time')
        .diff()
        .dropna()
        .reset_index()
        .melt(id_vars='Time', var_name='CTRL')
    )
    changes = changes[changes.value > 0].sort_values('Time')
    changes['Sequence'] = range(1, len(changes) + 1)
    return changes


@st.cache
def devc_groups(devc_meta: pd.DataFrame):
    id_vars = ['x', 'y', 'z', 'id', 'level']
    group_vars = [c for c in devc_meta.columns if c not in id_vars]

    groups = []
    for vals, idxs in devc_meta.groupby(group_vars).groups.items():
        group = dict(zip(group_vars, vals))
        group['ids'] = devc_meta.iloc[idxs]['id'].to_list()
        groups.append(group)

    return groups


@st.cache
def melt_and_merge(
    df: pd.DataFrame,
    meta: pd.DataFrame,
    id_vars: str='Time',
    var_name: str='devc',
    df_on: str='devc',
    meta_on: str='id',
) -> pd.DataFrame:
    return (
        df
        .melt(id_vars=id_vars, var_name=var_name)
        .merge(meta, left_on=df_on, right_on=meta_on)
    )


@st.cache
def get_subset(
    df: pd.DataFrame,
    ids: List[str],
    col: str='devc'
) -> pd.DataFrame:
    return df[df[col].isin(ids)]


def display_progress(start: float, cur: float, end: float) -> None:
    try:
        progress = (end - cur) / (end - start)
    except ZeroDivisionError:
        return
    st.write(f'{progress * 100:.1f}% Complete {cur} s / {end} s')
    st.progress(progress)


def display_timesteps(timestep_df: pd.DataFrame) -> None:
    if timestep_df.empty:
        st.write("Upload CHID.out to see more information")
        return
    else:
        chart(graphs.timesteps(timestep_df))


def display_hrr(hrr_df: pd.DataFrame) -> None:
    if hrr_df.empty:
        st.write("Upload CHID_hrr.csv to see HRR Graph")
        return
    else:
        chart(graphs.hrr_graph(hrr_df))


def display_ctrl(ctrl_df: pd.DataFrame) -> None:
    if ctrl_df.empty:
        st.write("Upload CHID_ctrl.csv to see CTRL Timeline")
        return
    else:
        changes = get_activation_times(ctrl_df)
        chart(graphs.ctrl_graph(changes))


def display_devc(
    devc_df: pd.DataFrame,
    devc_meta: pd.DataFrame,
) -> None:
    if devc_df.empty:
        st.write("Upload CHID_devc.csv to see DEVC Timelines")
        return

    groups = devc_groups(devc_meta)
    melted = melt_and_merge(devc_df, devc_meta)

    for group in groups:
        if group['make'] == 'null':
            subheader = group['qty']
        else:
            subheader = f"{group['qty']}: {group['make']}"

        st.subheader(subheader)

        subset = get_subset(melted, group['ids'])
        for level in subset.level.unique():
            chart(graphs.devc_graph(
                subset[subset.level == level],
                group['qty'],
            ))


def main():
    hrr_csv = file_uploader('Upload HRR csv')
    hrr_df = read_csv(hrr_csv)
    ctrl_csv = file_uploader('Upload CTRL csv')
    ctrl_df = read_csv(ctrl_csv)
    devc_csv = file_uploader('Upload DEVC csv')
    devc_df = read_csv(devc_csv)
    out_file = file_uploader('Upload .out file', ext='out')
    out_txt = ''
    if out_file is not None:
        out_txt = out_file.read()

    t_start, t_current, t_end = parse_times(hrr_df, ctrl_df, devc_df, out_txt)
    timestep_info = parse_timesteps(out_txt)
    devc_meta = parse_devc_meta(out_txt)

    display_progress(t_start, t_current, t_end)
    display_timesteps(timestep_info)
    display_hrr(hrr_df)
    display_ctrl(ctrl_df)
    display_devc(devc_df, devc_meta)


if __name__ == '__main__':
    main()
    st.sidebar.markdown('''
    ---
    Made with :heartpulse: by **Brian Cohan** 
    
    Please say hi :wave:
    
    * [LinkedIn](https://www.linkedin.com/in/briandcohan/)
    * [Twitter](https://twitter.com/BrianDCohan)
    ''')
