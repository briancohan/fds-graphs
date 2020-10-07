import io
from typing import Tuple

import pandas as pd
import parse
import streamlit as st

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

    st.write(t_start, t_current, t_end)
    st.write(timestep_info)
    st.write(devc_meta)


if __name__ == '__main__':
    main()
    st.sidebar.markdown('''
    ---
    Made with :heartpulse: by **Brian Cohan** 
    
    Please say hi :wave:
    
    * [LinkedIn](https://www.linkedin.com/in/briandcohan/)
    * [Twitter](https://twitter.com/BrianDCohan)
    ''')
