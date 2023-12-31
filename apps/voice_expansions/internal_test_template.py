""" A workbook to generating an internal testing survey.

Usage:
    $ PYTHONPATH=. streamlit run apps/voice_expansions/internal_test_template.py --runner.magicEnabled=false
"""
import io
import os
import time
import random
import pandas as pd
import streamlit as st
from st_files_connection import FilesConnection


num_audio = 40
gcs_audio_path = "wellsaid_labs_streamlit_data/voice_expansions/2023_q3/lyric_and_lee/audio"
gcs_csv_path = "wellsaid_labs_streamlit_data/voice_expansions/2023_q3/lyric_and_lee/metadata.csv"
gcs_responses_path = "wellsaid_labs_streamlit_data/voice_expansions/2023_q3/lyric_and_lee/responses"
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
            div[data-testid="stJson"] {
                display: none;
            }
            hr {
                margin: 1rem 0rem 2rem 0rem;
                vertical-align: top;
            }
          </style>
        """,
        unsafe_allow_html=True)

@st.cache_data
def load_subset():
    try:
        audio_csv = conn.read(gcs_csv_path, input_format="csv")

    except NameError:
        print("Audio CSV file not found")
        raise NameError
        return

    all_audio_ids = range(len(audio_csv))
    audio_subset = random.sample(all_audio_ids, k=num_audio)
    return audio_csv, audio_subset


def format_speaker_name(name):
    formatted_name = " ".join(list(string.capitalize() for string in str(name).split("_")))
    return formatted_name


def email_btn():
    form_email_input: str = st.session_state.form_email_input
    if form_email_input == "" or "@wellsaidlabs.com" not in form_email_input:
        st.warning("Please provide your email in the format x@wellsaidlabs.com")
    else:
        st.session_state.open_form = True
        st.cache_data.clear()

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

@st.cache_data(show_spinner="Getting your samples ready for you!")
def load_data():
    audio_csv, audio_subset = load_subset()
    for form_audio_id in range(num_audio):
        form_audio_id_adj = form_audio_id + 1 #adjust so starts with 1 not 0
        org_audio_id = audio_subset[form_audio_id]
        speaker = audio_csv.loc[audio_csv["Id"] == org_audio_id, "Speaker"].item()
        formatted_speaker = format_speaker_name(speaker)
        style = audio_csv.loc[audio_csv["Id"] == org_audio_id, "Session"].item().split(",")[2]
        script = audio_csv.loc[audio_csv["Id"] == org_audio_id, "Script"].item()
        spectrogram_model = audio_csv.loc[audio_csv["Id"] == org_audio_id, "Spectrogram Model"].item()
        signal_model = audio_csv.loc[audio_csv["Id"] == org_audio_id, "Signal Model"].item()

        audio_path = os.path.join(gcs_audio_path, f"{org_audio_id}.wav")
        audio_gcs = conn.open(audio_path, mode="rb")
        audio = io.BytesIO(audio_gcs.read())

        row = pd.Series({
            "Email": st.session_state.form_email_input,
            "Audio ID": org_audio_id,
            "Audio Path": audio_path,
            "Audio": audio,
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

def main():
    if "open_form" not in st.session_state:
        st.session_state.open_form = False
    if "form_disabled" not in st.session_state:
        st.session_state.form_disabled = False
    if "user_response" not in st.session_state:
        st.session_state.user_response = pd.DataFrame(columns=[
            "Email",
            "Audio ID",
            "Audio Path",
            "Audio"
            "Form Audio ID",
            "Speaker",
            "Style",
            "Script",
            "Spectrogram Model",
            "Signal Model",
            "Pass?",
            "Comments",
        ])
    if "listened" not in st.session_state:
        st.session_state.listened = [False for i in range(num_audio)]

    if not st.session_state.form_disabled:
        format_survey_style()
        st.title("Internal Testing Survey 🎧")
        st.caption(instructions)

        with st.form("form_email"):
            st.text_input(label="What is your WSL email?", key="form_email_input")
            st.form_submit_button("Get your audio!", on_click=email_btn, disabled=st.session_state.open_form)

        if st.session_state.open_form:
            with st.container():
                tab_names = [str(tab_num + 1) for tab_num in range(num_audio)]
                tab_names.append("Submit")
                tabs = st.tabs(tab_names)
                load_data()
                for form_audio_id in range(num_audio + 1):
                    with tabs[form_audio_id]:
                        if form_audio_id < num_audio:
                            form_audio_id_adj = form_audio_id + 1 #adjust so starts with 1 not 0

                            st.write(f'<p><span style="color:#38ef7d;font-weight:bold;">Audio:</span> {form_audio_id_adj} &emsp; \
                                    <span style="color:#38ef7d;font-weight:bold;">Speaker:</span> {st.session_state.user_response.loc[form_audio_id, "Speaker"]}. &emsp; \
                                    <span style="color:#38ef7d;font-weight:bold;">Style:</span> {st.session_state.user_response.loc[form_audio_id, "Style"]}</p>', unsafe_allow_html=True)
                            st.write(f'<span style="color:#38ef7d;font-weight:bold;">Script:</span> "{st.session_state.user_response.loc[form_audio_id, "Script"]}"</p>', unsafe_allow_html=True)
                            st.write(f'<hr style="border-bottom:1px solid #5734cf">', unsafe_allow_html=True)
                            col1, col2 = st.columns(2)

                            col1.audio(st.session_state.user_response.loc[form_audio_id, "Audio"])
                            col2.radio("Would you use this audio in your own work?", ["Yes", "No"], key=f"{form_audio_id_adj}", horizontal=True)
                            st.text_input(label="Additional Comments:", key=f"comments_{form_audio_id_adj}")

                            st.session_state.listened[form_audio_id] = st.checkbox("I have listened to this audio", key=f"listened_{form_audio_id_adj}")

                        elif form_audio_id == num_audio:
                            if all(st.session_state.listened):
                                st.write("Woohoo, you have listened to everything!")
                                st.write("Make sure to double check your answers before submitting - you can only submit once.")
                                st.button(
                                    "Submit your results!",
                                    on_click = update_results,
                                    disabled = st.session_state.form_disabled
                                )
                            else:
                                st.write("Whoops looks like you haven't marked all of the audio as listened to, you still seem to be missing:")
                                missing_str = ""
                                for i in range(num_audio):
                                    if not st.session_state.listened[i]:
                                        missing_str += f" {i+1},"
                                st.write(missing_str[:-1]) # remove last comma

    else:
        st.info("Your results have been submitted! If you need to change anything please slack Jessica Petrochuk \
            or send an email to jessicap@wellsaidlabs.com. You can also refresh this page to take the survey again with\
            a new set of audio. Thanks again!")


if __name__ == "__main__":
    main()