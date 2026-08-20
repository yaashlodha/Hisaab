import datetime
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

st.set_page_config(page_title="Hisaab Tracker", page_icon="📝", layout="centered")
st.title("📝 Expense Entry Form")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource
def get_sheet():
    # If running on Streamlit Cloud, read from st.secrets
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
    else:
        # If running locally, read credentials.json
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    
    client = gspread.authorize(creds)
    return client.open("Hisaab")  # Replace with your exact Google Sheet title

try:
    spreadsheet = get_sheet()
except Exception as e:
    st.error(f"Error connecting to Google Sheets: {e}")
    st.stop()

PEOPLE = ["Praveen", "Mehul", "Rahil", "Deesha", "Hridaya", "Sayam"]

with st.form("entry_form", clear_on_submit=True):
    person = st.selectbox("Select Person", PEOPLE)
    date_val = st.date_input("Date", value=datetime.date.today())
    owed_by_me = st.number_input("Amount Owed by Me", min_value=0.0, step=10.0, format="%.2f")
    owed_by_them = st.number_input("Amount Owed by Them", min_value=0.0, step=10.0, format="%.2f")
    reason = st.text_input("Reason / Notes")

    submit_button = st.form_submit_button("Submit Entry")

if submit_button:
    try:
        ws = spreadsheet.worksheet(person)
        row_data = [str(date_val), owed_by_me, owed_by_them, reason]
        ws.append_row(row_data, value_input_option="USER_ENTERED")
        st.success(f"Entry saved to **{person}**'s sheet successfully!")
    except Exception as e:
        st.error(f"Failed to append entry: {e}")