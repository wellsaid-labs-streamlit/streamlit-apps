""" A workbook to generating a test app.

Usage:
    $ PYTHONPATH=. streamlit run apps/test_app.py --runner.magicEnabled=false
"""

import streamlit as st

def main():
    st.header("Hello Wellsaid")

if __name__ == "__main__":
    main()