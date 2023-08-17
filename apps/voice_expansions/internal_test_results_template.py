""" A workbook to generating an internal testing survey results.

Usage:
    $ PYTHONPATH=. streamlit run apps/voice_expansions/internal_test_results_template.py --runner.magicEnabled=false
"""
import io
import os
import time
import random
import pandas as pd
import streamlit as st
from st_files_connection import FilesConnection


gcs_audio_path = "wellsaid_labs_streamlit_data/voice_expansions/2023_q3/lyric_and_lee/audio"
gcs_csv_path = "wellsaid_labs_streamlit_data/voice_expansions/2023_q3/lyric_and_lee/metadata.csv"
gcs_responses_path = "wellsaid_labs_streamlit_data/voice_expansions/2023_q3/lyric_and_lee/responses/*.csv"
conn = st.experimental_connection('gcs', type=FilesConnection)

def main():
    st.header("Results")
    files = list(conn.fs.glob(gcs_responses_path))
    for file in files:
        print(file)

if __name__ == "__main__":
    main()