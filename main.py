#!/usr/bin/env python3
__description__ =\
"""
Purpose: Streamlit wrapper for sanger-sequence-trim.
"""
__author__ = "Erick Samera"
__version__ = "1.0.0"
__comments__ = "stable enough"
# --------------------------------------------------
import streamlit as st
import pandas as pd
# --------------------------------------------------
class App:
    def __init__(self):
        """
        """
    def _init_page(self) -> None:
        """
        Function instantiates the main page.
        """
        self.title = "sanger-sequence-trim"
        st.set_page_config(
            page_title=f"abi-sauce | {self.title}",
            page_icon='🧪',
            layout='wide',
            initial_sidebar_state='collapsed')
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"][aria-expanded="true"]{
                min-width: 450px;
                max-width: 450px;
            }""",
            unsafe_allow_html=True,
            )   
        self._init_sidebar()
        self._init_main_window()
    def _init_sidebar(self) -> None:
        """
        Instantiate the sidebar.
        """
    
        with st.sidebar:
            st.title(f"🧪 sqx-editor")
            st.success('Select one of the apps above to get started!')
    def _init_main_window(self) -> None:
        """
        """
        st.title('🧪 `sqx-editor`!')
        st.markdown('These are a set of open-source tools to make handling electropherogram data easier.')
        st.markdown('Check out my GitHub with the link below for some of my other projects.')
        st.caption(f'[@{__author__}](https://github.com/ericksamera)\t|\tv{__version__}\t|\t{__comments__}')

        data_df = pd.DataFrame([
            #{"check": "","vial": "","Action": "","Acq. method": "","sample-type": "","Level": "","Inj/Vial": "","Volume": "","inj-source": "","Sample name": "","Data file": ""},
            {"check": True, "vial": 0, "sample-type": "🟢 Sample", "inj-source": "HipAls",}

        ])

        edited_df = st.data_editor(
            data_df,
            use_container_width=True,
            column_config={
                "check": st.column_config.CheckboxColumn(),
                "vial": st.column_config.NumberColumn(),
                "sample-type": st.column_config.SelectboxColumn(
                    "Sample type",
                    width="medium",
                    default="🟢 Sample",
                    options=[
                        "🟢 Sample",
                        "⚪ Blank",
                        "🟠 Double blank",
                        "🔵 Cal. Std.",
                        "🟣 QC check",
                        "⚫ Spike",
                        "🟤 Sys. Suit.",
                    ],
                    required=True,
                ),
                "inj-source": st.column_config.SelectboxColumn(
                    "Injection source",
                    width="medium",
                    default="HipAls",
                    options=[
                        "HipAls",
                        "External",
                        "No Injection/Instrument Blank"
                    ],
                    required=True,
                )
            },
            hide_index=True,
            num_rows="dynamic",
        )

        return None
# --------------------------------------------------
if __name__=="__main__":
    streamlit_app = App()
    streamlit_app._init_page()