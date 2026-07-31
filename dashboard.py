import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="SentryGate — Safety Gateway Dashboard", layout="wide")

DB_PATH = "sentrygate.db"

def load_data(query: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.warning(f"Error loading data: {e}. Has the database been created yet?")
        return pd.DataFrame()

st.title("SentryGate — Safety Gateway Dashboard")

col1, col2 = st.columns([1, 10])
with col1:
    if st.button("Refresh"):
        st.rerun()

st.divider()

# Load requests and responses
requests_df = load_data("SELECT * FROM requests")
responses_df = load_data("SELECT * FROM responses")

st.header("1. Traffic Overview")
if not requests_df.empty:
    total_requests = len(requests_df)
    
    # Input block rate
    input_blocks = requests_df['input_blocked'].sum() if 'input_blocked' in requests_df.columns else 0
    input_block_rate = (input_blocks / total_requests * 100) if total_requests > 0 else 0
    
    # Output block rate (from responses)
    output_blocks = responses_df['output_blocked'].sum() if not responses_df.empty and 'output_blocked' in responses_df.columns else 0
    total_responses = len(responses_df)
    output_block_rate = (output_blocks / total_responses * 100) if total_responses > 0 else 0
    
    # Total blocked
    total_blocked = input_blocks + output_blocks

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Requests", total_requests)
    m2.metric("Input Block Rate", f"{input_block_rate:.1f}%")
    m3.metric("Output Block Rate", f"{output_block_rate:.1f}%")
    m4.metric("Total Blocked Overall", total_blocked)

    st.subheader("Block Count by Category")
    # Combine input and output categories
    categories = []
    if 'input_block_category' in requests_df.columns:
        categories.extend(requests_df['input_block_category'].dropna().tolist())
    if not responses_df.empty and 'output_block_category' in responses_df.columns:
        categories.extend(responses_df['output_block_category'].dropna().tolist())
    
    if categories:
        cat_df = pd.DataFrame(categories, columns=['Category'])
        cat_counts = cat_df['Category'].value_counts()
        st.bar_chart(cat_counts)
    else:
        st.info("No blocked categories to display yet.")

    st.subheader("Requests per Day")
    if 'timestamp' in requests_df.columns:
        # Convert to datetime and extract date
        requests_df['date'] = pd.to_datetime(requests_df['timestamp']).dt.date
        date_counts = requests_df.groupby('date').size()
        
        if len(date_counts) < 2:
            st.info("Not enough data yet for a daily trend — will populate as more requests come in.")
        else:
            st.line_chart(date_counts)
else:
    st.info("No requests logged yet.")

st.divider()

st.header("2. Recent Activity")
if not requests_df.empty and not responses_df.empty:
    # Join on request_id
    merged_df = pd.merge(requests_df, responses_df, left_on='id', right_on='request_id', how='left', suffixes=('_req', '_res'))
    
    # Sort by timestamp descending
    if 'timestamp_req' in merged_df.columns:
        merged_df = merged_df.sort_values(by='timestamp_req', ascending=False).head(50)
        
        # Columns to display
        display_cols = [
            'timestamp_req', 'user_id', 'user_input', 
            'input_blocked', 'input_block_reason', 
            'output_blocked', 'output_block_reason', 'final_response'
        ]
        # Keep only cols that exist
        available_cols = [col for col in display_cols if col in merged_df.columns]
        table_df = merged_df[available_cols].copy()
        
        # Filter selectbox
        filter_opt = st.selectbox("Filter Activity", ["All", "Blocked only", "Allowed only"])
        if filter_opt == "Blocked only":
            # Check if either is true
            blocked_mask = (table_df.get('input_blocked') == True) | (table_df.get('output_blocked') == True)
            table_df = table_df[blocked_mask]
        elif filter_opt == "Allowed only":
            allowed_mask = (table_df.get('input_blocked') != True) & (table_df.get('output_blocked') != True)
            table_df = table_df[allowed_mask]
            
        st.dataframe(table_df, use_container_width=True)
else:
    st.info("No activity to display yet.")


st.divider()

st.header("3. Eval Suite Results")
eval_df = load_data("SELECT * FROM eval_runs")
if eval_df.empty:
    st.info("No eval runs yet — run `python eval/run_eval.py` to generate results.")
else:
    total_evals = len(eval_df)
    passed_evals = eval_df['passed'].sum() if 'passed' in eval_df.columns else 0
    pass_rate = (passed_evals / total_evals * 100) if total_evals > 0 else 0
    
    st.metric("All-Time Eval Pass Rate", f"{pass_rate:.1f}%")
    
    st.subheader("All Eval Runs")
    if 'timestamp' in eval_df.columns:
        eval_df = eval_df.sort_values(by='timestamp', ascending=False)
        
    display_cols_eval = ['test_case_id', 'category', 'expected', 'actual', 'passed', 'timestamp']
    available_eval_cols = [col for col in display_cols_eval if col in eval_df.columns]
    
    st.dataframe(eval_df[available_eval_cols], use_container_width=True)
