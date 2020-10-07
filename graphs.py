import altair as alt
import pandas as pd


def hrr_graph(df: pd.DataFrame) -> alt.Chart:

    line = alt.Chart(df).mark_line().encode(
        x=alt.X('Time:Q', title='Time [sec]'),
        y=alt.Y('HRR', title='HRR [kW]'),
    )

    return line


def ctrl_graph(df: pd.DataFrame) -> alt.Chart:

    point = alt.Chart(df).mark_point().encode(
        x=alt.X(
            'Time:Q',
            title='Time [sec]',
        ),
        y='Sequence:O',
        tooltip=['CTRL', 'Time']
    )

    text = point.mark_text(
        align='left',
        baseline='middle',
        dx=10,
    ).encode(text='CTRL')

    return point + text
