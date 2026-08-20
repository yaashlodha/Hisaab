import datetime
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Hisaab Tracker", page_icon="💰", layout="centered"
)

# ----------------- Authentication Gate -----------------
# ----------------- Authentication Gate -----------------
ADMIN_PASSWORD = st.secrets.get("APP_PASSWORD", "mysecretpassword123")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    # Use .get() to safely retrieve the value without raising AttributeError
    if st.session_state.get("password_input", "") == ADMIN_PASSWORD:
        st.session_state.authenticated = True
    else:
        st.session_state.authenticated = False
        st.error("❌ Incorrect password. Please try again.")
# -------------------------------------------------------

if not st.session_state.authenticated:
    st.title("🔒 Login Required")
    st.text_input(
        "Enter Password:",
        type="password",
        on_change=check_password,
        key="password_input",
    )
    st.button("Log In", on_click=check_password)
    st.stop()  # Halt execution until authenticated

# ----------------- Authenticated App -----------------
st.sidebar.button(
    "Log Out",
    on_click=lambda: st.session_state.update(authenticated=False),
)

st.title("💰 Hisaab Tracker")

# Google Sheets Authentication
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource
def get_sheet():
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
    else:
        creds = Credentials.from_service_account_file(
            "credentials.json", scopes=SCOPES
        )

    client = gspread.authorize(creds)
    return client.open("Hisaab")


try:
    spreadsheet = get_sheet()
except Exception as e:
    st.error(f"Error connecting to Google Sheets: {e}")
    st.stop()

PEOPLE = ["Praveen", "Mehul", "Rahil", "Deesha", "Hridaya", "Sayam"]

# Tab Navigation
tab_entry, tab_status, tab_overview = st.tabs(
    ["➕ Add Entry", "🔍 Check Person", "📊 All Totals"]
)

# 1. Add Entry Tab
with tab_entry:
    with st.form("entry_form", clear_on_submit=True):
        person = st.selectbox("Select Person", PEOPLE)
        date_val = st.date_input("Date", value=datetime.date.today())
        owed_by_me = st.number_input(
            "Amount Owed by Me (₹)", min_value=0.0, step=10.0, format="%.2f"
        )
        owed_by_them = st.number_input(
            "Amount Owed by Them (₹)", min_value=0.0, step=10.0, format="%.2f"
        )
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

# 2. Individual Person Balance Tab
with tab_status:
    selected_person = st.selectbox(
        "Choose a person to check balance:", PEOPLE, key="check_person"
    )

    if st.button("Fetch Balance"):
        try:
            ws = spreadsheet.worksheet(selected_person)
            total_val = ws.acell("E2").value
            total_amount = float(total_val) if total_val else 0.0

            if total_amount > 0:
                st.metric(
                    label=f"Balance with {selected_person}",
                    value=f"₹{total_amount:,.2f}",
                    delta="They owe you",
                    delta_color="normal",
                )
            elif total_amount < 0:
                st.metric(
                    label=f"Balance with {selected_person}",
                    value=f"₹{abs(total_amount):,.2f}",
                    delta="You owe them",
                    delta_color="inverse",
                )
            else:
                st.metric(
                    label=f"Balance with {selected_person}",
                    value="₹0.00",
                    delta="All settled up",
                    delta_color="off",
                )

            records = ws.get_all_values()
            if len(records) > 1:
                df = pd.DataFrame(records[1:], columns=records[0])
                st.write("**Recent Entries:**")
                st.dataframe(df.tail(5), use_container_width=True)

        except Exception as e:
            st.error(f"Could not load balance: {e}")

# 3. Overview Dashboard Tab
with tab_overview:
    if st.button("Refresh All Balances"):
        with st.spinner("Fetching data from sheets..."):
            balances = []
            for name in PEOPLE:
                try:
                    val = spreadsheet.worksheet(name).acell("E2").value
                    numeric_val = float(val) if val else 0.0
                except Exception:
                    numeric_val = 0.0
                balances.append(
                    {"Person": name, "Net Balance (₹)": numeric_val}
                )

            df_all = pd.DataFrame(balances)
            grand_total = df_all["Net Balance (₹)"].sum()

            st.dataframe(df_all, use_container_width=True)
            st.metric(
                label="Overall Net Total (All Sheets)",
                value=f"₹{grand_total:,.2f}",
            )