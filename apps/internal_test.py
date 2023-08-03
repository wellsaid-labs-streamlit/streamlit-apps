""" A workbook to generating an internal testing survey.

Usage:
    $ PYTHONPATH=. streamlit run apps/internal_test.py --runner.magicEnabled=false
"""
import io
import os
import time
import random
import pandas as pd
import streamlit as st
from st_files_connection import FilesConnection

# Set these variables to start
num_audio = 20
gcs_audio_path = "wellsaid_labs_streamlit_data/test/test_audio"
gcs_csv_path = "wellsaid_labs_streamlit_data/test/test.csv"
gcs_responses_path = "wellsaid_labs_streamlit_data/test/test_responses"
conn = st.experimental_connection('gcs', type=FilesConnection)

instructions = "Thank you so much for volunteering to test out these new styles and voices - we are \
            really excited to hear your feedback! As you go through all of the audio provided \
              please assess whether or not you would use this audio in your own work. Feel free to \
                also leave any additional comments. Thanks again and happy listening!"

def format_survey_style():
    st.markdown(
        """
          <style>
            [role=tab][aria-selected="true"] {
                color: #38ef7d;
            }
            [role=tablist] :is([role=presentation]){
                background-color: #38ef7d !important;
            }
            [role=radiogroup] label:has(input[type="radio"]:checked) div:first-of-type {
                background-color: #38ef7d !important;
            }
            [role=radiogroup] label:has(input[type="radio"]:checked) div:first-of-type div{
                background-color: white !important;
            }
            p {
                font-size: 16px !important;
            }
            label div p {
                font-weight: bold;
            }
          </style>
        """,
        unsafe_allow_html=True)


def format_speaker_name(name):
    formatted_name = " ".join(list(string.capitalize() for string in str(name).split("_")))
    return formatted_name


def email_btn():
    form_email_input: str = st.session_state.form_email_input
    if form_email_input == "" or "@wellsaidlabs.com" not in form_email_input:
        st.warning("Please provide your email in the format x@wellsaidlabs.com")
    else:
        st.session_state.open_form = True
        st.session_state

def update_results():
    user_response = st.session_state.user_response
    email = user_response.iloc[0].loc["Email"]
    timestr = time.strftime("%Y%m%d-%H%M%S")

    for i in range(num_audio):
        key = f"{i + 1}"
        if st.session_state[key] == "Yes":
            user_response.at[i, "Pass?"] = 1
            user_response.at[i, "Comments"] = st.session_state[f"comments_{i + 1}"]
        elif st.session_state[key] == "No":
            user_response.at[i, "Pass?"] = 0
            user_response.at[i, "Comments"] = st.session_state[f"comments_{i + 1}"]
    
    response_file_name = f"{email}_{timestr}.csv"
    response_path = os.path.join(gcs_responses_path, response_file_name)
    with conn.fs.open(response_path, 'wb') as f:
        user_response.to_csv(f, index=False)

    st.session_state.form_disabled = True

def main():
    try:
        audio_csv = conn.read(gcs_csv_path, input_format="csv")

    except NameError:
        print("Audio CSV file not found")
        raise NameError
        return

    # Set up session states
    if "open_form" not in st.session_state:
        st.session_state.open_form = False
    if "form_disabled" not in st.session_state:
        st.session_state.form_disabled = False
    if "user_response" not in st.session_state:
        st.session_state.user_response = pd.DataFrame(columns=[
            "Email",
            "Audio ID",
            "Form Audio ID",
            "Speaker",
            "Style",
            "Script",
            "Spectrogram Model",
            "Signal Model",
            "Pass?",
            "Comments"
        ])
    container = st.empty()
    if not st.session_state.form_disabled:
        format_survey_style()
        st.title("Internal Testing Survey 🎧")
        st.caption(instructions)

        with st.form("form_email"):
            st.text_input(label="What is your WSL email?", key="form_email_input")
            st.form_submit_button("Get your audio!", on_click=email_btn, disabled=st.session_state.open_form)

        if st.session_state.open_form:
            with st.form("form_audio"):
                with st.spinner("Pulling together some audio files for you!"):
                    all_audio_ids = range(len(audio_csv))
                    audio_subset = random.choices(all_audio_ids, k=num_audio)
            
                    tab_names = [str(tab_num + 1) for tab_num in range(num_audio)]
                    tabs = st.tabs(tab_names)

                for form_audio_id in range(num_audio):
                    with tabs[form_audio_id]:
                        form_audio_id_adj = form_audio_id + 1 #adjust so starts with 1 not 0
                        org_audio_id = audio_subset[form_audio_id]
                        speaker = audio_csv.loc[audio_csv["Id"] == org_audio_id, "Speaker"].item()
                        style = audio_csv.loc[audio_csv["Id"] == org_audio_id, "Session"].item().split(",")[2]
                        script = audio_csv.loc[audio_csv["Id"] == org_audio_id, "Script"].item()
                        spectrogram_model = audio_csv.loc[audio_csv["Id"] == org_audio_id, "Spectrogram Model"].item()
                        signal_model = audio_csv.loc[audio_csv["Id"] == org_audio_id, "Signal Model"].item()
                        formatted_speaker = format_speaker_name(speaker)
                        # st.write(f'<p><span style="color:#38ef7d;font-weight:bold;">Audio:</span> {form_audio_id_adj} &emsp; \
                        #         <span style="color:#38ef7d;font-weight:bold;">Speaker:</span> {formatted_speaker}. &emsp; \
                        #         <span style="color:#38ef7d;font-weight:bold;">Style:</span> {style} &emsp; \
                        #         <span style="color:#38ef7d;font-weight:bold;">Script:</span> "{script}"</p>', unsafe_allow_html=True)
                        st.markdown("""---""")
                        col1, col2 = st.columns(2)
                        
                        audio_path = os.path.join(gcs_audio_path, f"{org_audio_id}.wav") # TODO: fix this to org id
                        audio_gcs = conn.open(audio_path, mode="rb")
                        audio = io.BytesIO(audio_gcs.read())
                        col1.audio(audio)
                        col2.radio("Would you use this audio in your own work?", ["Yes", "No"], key=f"{form_audio_id_adj}", horizontal=True)
                        st.text_input(label="Additional Comments:", key=f"comments_{form_audio_id_adj}")
                        # st.write(f'<hr style="border-bottom:3px solid #5734cf">', unsafe_allow_html=True)
                        row = pd.Series({
                            "Email": st.session_state.form_email_input,
                            "Audio ID": org_audio_id,
                            "Form Audio ID": form_audio_id_adj,
                            "Speaker": formatted_speaker,
                            "Style": style,
                            "Script": script,
                            "Spectrogram Model": spectrogram_model,
                            "Signal Model": signal_model,
                            "Pass?": 0,
                            "Comments": ""
                        })
                        st.session_state.user_response = pd.concat([st.session_state.user_response, row.to_frame().T], ignore_index=True)

                # st.write("Make sure to double check your answers before submitting - you can only submit once.")
                st.form_submit_button(
                    "Submit your results!",
                    on_click = update_results,
                    disabled = st.session_state.form_disabled
                )

    else:
        st.info("Your results have been submitted! If you need to change anything please slack Jessica Petrochuk \
            or send an email to jessicap@wellsaidlabs.com. You can also refresh this page to take the survey again with\
            a new set of audio. Thanks again!")


if __name__ == "__main__":
    main()