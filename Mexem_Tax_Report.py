import streamlit as st
import pandas as pd
import os

# Set page config
dashboard_title = "MEXEM (IBKR) Tax Report Dashboard"
st.set_page_config(page_title=dashboard_title, layout="wide")
st.title(dashboard_title)
st.caption("Analyze and visualize your MEXEM/IBKR activity report for tax and financial insights.")

# Interactive file uploader for the CSV
uploaded_file = st.file_uploader(
    "Upload your MEXEM report CSV file",
    type=["csv"],
    help="Upload the exported MEXEM/IBKR activity report CSV."
)

if uploaded_file is not None:
    # Save uploaded file to a temporary path for parsing
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.read())
        report_path = tmp.name
else:
    # Optionally, use a default file for local dev/testing
    default_path = r"C:\Users\david\Documents\Data_for_Analysis\MEXEM\[MEXEM]Resoconto_U16517211_20241129_20250613.csv"
    if os.path.exists(default_path):
        st.info("No file uploaded. Using default local file for demonstration.")
        report_path = default_path
    else:
        st.warning("Please upload a MEXEM report CSV file to continue.")
        st.stop()

# Custom parser for MEXEM multi-section CSV

def extract_section(filepath, section_name):
    """
    Extracts a section from the MEXEM CSV by section_name (e.g., 'Dettaglio eseguiti').
    Returns a DataFrame or None if not found.
    Handles duplicate/empty column names and repeated headers.
    """
    import csv
    section_lines = []
    in_section = False
    header = None
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            if line.startswith(section_name + ",Header"):
                in_section = True
                header_candidate = [h.strip() for h in next(csv.reader([line.strip()]))][2:]
                # Only set header if not already set
                if header is None:
                    header = header_candidate
                continue
            if in_section:
                # Skip repeated headers inside the section
                if line.startswith(section_name + ",Header"):
                    continue
                if line.startswith(section_name + ",Data") or line.startswith(section_name + ",SubTotal") or line.startswith(section_name + ",Total"):
                    row = [h.strip() for h in next(csv.reader([line.strip()]))][2:]
                    section_lines.append(row)
                elif not line.strip() or not line.startswith(section_name):
                    break  # End of section
    if section_lines and header:
        # Fix empty and duplicate column names
        clean_header = []
        col_count = {}
        for i, col in enumerate(header):
            col = col if col else f"Unnamed_{i+1}"
            if col in col_count:
                col_count[col] += 1
                col = f"{col}_{col_count[col]}"
            else:
                col_count[col] = 1
            clean_header.append(col)
        import pandas as pd
        df = pd.DataFrame(section_lines, columns=clean_header)
        return df
    return None

# Use the custom parser to extract the 'Dettaglio eseguiti' section
trades_df = extract_section(report_path, "Dettaglio eseguiti")

if trades_df is None or trades_df.empty:
    st.error("Could not extract 'Dettaglio eseguiti' (executed trades) section from the report.")
    st.stop()

# Show quick summary for trades
with st.expander("ℹ️ About this dashboard", expanded=True):
    st.write("""
    - This dashboard helps you analyze your MEXEM/IBKR activity report for tax-relevant information.
    - It auto-detects and parses the 'Dettaglio eseguiti' (executed trades) section for transactions.
    - Use the tabs below to explore your data and download filtered results for your tax records.
    """)

st.subheader("Executed Trades Overview")
st.write(f"**Rows:** {trades_df.shape[0]}  |  **Columns:** {trades_df.shape[1]}")
st.dataframe(trades_df.head(10))

# Tabs for analysis
# (You can expand this to other sections as needed)
tabs = st.tabs(["All Trades"])

with tabs[0]:
    st.header("All Executed Trades")
    st.dataframe(trades_df)
    st.download_button("Download Executed Trades as CSV", trades_df.to_csv(index=False), file_name="mexem_executed_trades.csv")

# --- Raw Data Expander ---
with st.expander("Show raw data (full table)"):
    st.dataframe(trades_df)

st.caption("This dashboard is for informational purposes only. Always consult a tax professional for your specific situation.")
