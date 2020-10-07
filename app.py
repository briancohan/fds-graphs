import streamlit as st
import pandas as pd
import altair as alt

st.header("It Worked!")

df = pd.DataFrame({
    'x': [1, 2, 3, 4, 5, 6, 7, 8, 9],
    'y': [1, 2, 3, 2, 1, 2, 3, 2, 1],
})
st.altair_chart(
    alt.Chart(df).mark_line().encode(x='x', y='y'),
    use_container_width=True
)