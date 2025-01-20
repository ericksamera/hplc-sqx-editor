#!/usr/bin/env python3
__description__ =\
"""
Purpose: Streamlit wrapper for sanger-sequence-trim.
"""
__author__ = ["Erick Samera", "Kevin Saulog"]
__version__ = "1.0.0"
__comments__ = "stable enough"
# --------------------------------------------------
import streamlit as st
import io
import hashlib
import xml.etree.ElementTree as ET
import zipfile
import pathlib
import shutil
import pandas as pd
# --------------------------------------------------
class SampleListEntry:
    def __init__(self, sample_name, sample_type, acquisition_method, vial, volume):
        """
        Represents a single sample entry in the SampleListPart.
        """
        self.sample_name = sample_name
        self.sample_type = sample_type
        self.acquisition_method = acquisition_method
        self.vial = vial
        self.volume = volume
# --------------------------------------------------
class App:
    def __init__(self):
        pass

    def _init_page(self) -> None:
        """
        Sets up page config, sidebar, and main window. 
        If the user has not uploaded or selected a file yet,
        it displays the file upload interface; otherwise, it updates the table.
        """
        self.title = "sqx-editor"
        st.set_page_config(
            page_title=f"{self.title}",
            page_icon='🧪',
            layout='wide',
            initial_sidebar_state='collapsed'
        )
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"][aria-expanded="true"] {
                min-width: 450px;
                max-width: 450px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        self._init_sidebar()
        self._init_main_window()

        if 'SAMPLES_LIST' not in st.session_state: self._init_file_uploader()
        else: self._update_plot()

    def _init_sidebar(self) -> None:
        """
        Instantiate the sidebar.
        """
        with st.sidebar:
            st.title("🧪 sqx-editor")
            st.success('Select one of the apps above to get started!')

    def _init_main_window(self) -> None:
        """
        Set up the main window content at the top of the page.
        """
        st.title(f'🧪 `{self.title}`')
        
        author_text = '; '.join([f"[@{author}]({git_link})" for author, git_link in zip(__author__, ("https://github.com/ericksamera", "https://github.com/ksaulog"))])
        st.caption(f'{author_text} | v{__version__} | {__comments__}')
        st.markdown('These are a set of open-source tools to make handling electropherogram data easier.')
        st.divider()

    def _reset_temp_dir(self) -> None:
        """
        Clears and recreates a temp directory for storing extracted files.
        """
        st.session_state.TEMP_DIR = pathlib.Path(__file__).parent.joinpath('temp')
        if st.session_state.TEMP_DIR.exists(): shutil.rmtree(st.session_state.TEMP_DIR)
        st.session_state.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    def _process_sqx_file(self, file_obj: io.BytesIO, file_name: str) -> None:
        """
        Centralizes file saving, extraction, and setting up the SAMPLES_LIST in session state.
        """
        self._reset_temp_dir()
        zip_path = st.session_state.TEMP_DIR.joinpath(file_name)
        with open(zip_path, 'wb') as temp_write:
            temp_write.write(file_obj.read())

        extract_dir = st.session_state.TEMP_DIR.joinpath('extracted')
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        st.toast(f"File '{file_name}' processed successfully.")
        st.session_state.SAMPLES_LIST = self.parse_sample_list_part()

    def _init_file_uploader(self) -> None:
        """
        Displays a file uploader and a button to create a sequence from a local template.
        """
        col1, col2 = st.columns(2)

        with col1:
            st.subheader('Upload sequence file (`.sqx`)')
            uploaded_file = st.file_uploader(
                'Upload `.sqx` file',
                type=['sqx'],
                accept_multiple_files=False
            )
            if uploaded_file:
                st.button(
                    "Unzip File",
                    on_click=self._process_sqx_file,
                    args=(uploaded_file, uploaded_file.name)
                )

        with col2:
            st.subheader("Create new sequence file")
            st.text("Use this option to create a new file.")
            st.button("Create from Template", on_click=self._create_from_template)

    def _create_from_template(self) -> None:
        """
        Creates a new sequence table using the local template `.sqx` file and 
        processes it like an uploaded file.
        """
        template_file_path = pathlib.Path(__file__).parent / "template" / "HPLC1-2025-01-13 HPLC Training.sqx"
        if not template_file_path.exists():
            st.error("Template `.sqx` file not found.")
            return

        with open(template_file_path, "rb") as f:
            file_bytes = f.read()

        template_file = io.BytesIO(file_bytes)
        template_file.name = template_file_path.name

        self._process_sqx_file(template_file, template_file.name)

    def parse_sample_list_part(self) -> list:
        """
        Parses the SampleListPart XML from the extracted folder and returns a list of SampleListEntry objects.
        """
        file_path = st.session_state.TEMP_DIR.joinpath('extracted', 'SampleListPart', 'SampleListPart')
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        tree = ET.parse(file_path)
        root = tree.getroot()
        namespace = {'ns': "http://schemas.datacontract.org/2004/07/Agilent.OpenLAB.Acquisition.AcquisitionMethodSequence"}

        samples = []
        for entry in root.findall('ns:anyType', namespace):
            sample_name = entry.findtext('ns:SampleName', default=None, namespaces=namespace)
            sample_type = entry.findtext('ns:SampleType', default=None, namespaces=namespace)
            acquisition_method = entry.findtext('ns:AcquisitionMethod', default=None, namespaces=namespace)
            vial = entry.findtext('ns:Vial', default=None, namespaces=namespace)
            volume = entry.findtext('ns:Volume', default=None, namespaces=namespace)

            sample = SampleListEntry(
                sample_name=sample_name,
                sample_type=sample_type,
                acquisition_method=acquisition_method,
                vial=vial,
                volume=volume
            )
            samples.append(sample)

        return samples

    def _samples_to_dict(self, samples: list) -> list:
        """
        Converts a list of SampleListEntry objects to a list of dictionaries for display in the data editor.
        """
        return [
            {
                "check": True,
                "vial": sample.vial,
                "action": "Inject",
                "acq-method": sample.acquisition_method,
                "sample-type": sample.sample_type,
                "level": "",
                "inj-vial": 1,
                "volume": sample.volume if sample.volume else "Use Method",
                "inj-source": "HipAls",
                "sample-name": sample.sample_name,
                "data-file": ""
            }
            for sample in samples
        ]

    def _save_edits_and_get_zip(self) -> bytes:
        """
        1) Updates the XML with any edits,
        2) Updates the .chk hash file,
        3) Zips up the edited directory,
        4) Returns the ZIP as bytes.
        """
        if "SAMPLES_LIST" not in st.session_state:
            st.error("No samples to save. Upload and edit a file first.")
            return b""

        edited_df = st.session_state.EDITED_DF
        xml_path = st.session_state.TEMP_DIR.joinpath("extracted", "SampleListPart", "SampleListPart")
        if not xml_path.exists():
            st.error("SampleListPart XML file not found.")
            return b""

        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = {'ns': "http://schemas.datacontract.org/2004/07/Agilent.OpenLAB.Acquisition.AcquisitionMethodSequence"}
        for i, entry in enumerate(root.findall('ns:anyType', ns)):
            if i < len(edited_df):
                entry.find('ns:SampleName', ns).text = edited_df.loc[i, "sample-name"]
                entry.find('ns:SampleType', ns).text = edited_df.loc[i, "sample-type"]
                entry.find('ns:AcquisitionMethod', ns).text = edited_df.loc[i, "acq-method"]
                entry.find('ns:Vial', ns).text = edited_df.loc[i, "vial"]
                entry.find('ns:Volume', ns).text = str(edited_df.loc[i, "volume"])

        tree.write(xml_path, encoding="utf-8", xml_declaration=True)

        chk_path = xml_path.parent.joinpath("SampleListPart.chk")
        with open(xml_path, 'rb') as f:
            contents = f.read()
        sha1_hash = hashlib.sha1(contents).digest()
        with open(chk_path, 'wb') as f:
            f.write(sha1_hash)

        # Zip the edited files
        zip_buffer = io.BytesIO()
        extracted_dir = st.session_state.TEMP_DIR.joinpath("extracted")
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in extracted_dir.rglob("*"):
                arcname = file_path.relative_to(extracted_dir)
                zipf.write(file_path, arcname=arcname)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    def _update_plot(self) -> None:
        """
        Displays the table, captures edits, and provides a single download button
        that triggers XML and hash updates, then returns a ZIP.
        """

        data_dicts = self._samples_to_dict(st.session_state.SAMPLES_LIST)
        data_df = pd.DataFrame(data_dicts)

        edited_df = st.data_editor(
            data_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "check": st.column_config.CheckboxColumn(
                    " ",
                    default=False,
                    width="small",
                ),
                "vial": st.column_config.TextColumn("Vial"),
                "action": st.column_config.TextColumn(
                    "Action",
                    width="small",
                    default="Inject",
                ),
                "acq-method": st.column_config.TextColumn(
                    "Acq. method",
                    width="medium",
                    default="Inject",
                ),
                "sample-type": st.column_config.SelectboxColumn(
                    "Sample type",
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
                "level": st.column_config.TextColumn(
                    "Level",
                    width="small",
                    default="",
                ),
                "inj-vial": st.column_config.NumberColumn(
                    "Inj/Vial",
                    width="small",
                    default=1,
                ),
                "volume": st.column_config.NumberColumn(
                    "Volume",
                    width="medium",
                    default=1,
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
                ),
                "sample-name": st.column_config.TextColumn(
                    "Sample name",
                    width="large",
                    default="",
                ),
                "data-file": st.column_config.TextColumn(
                    "Data file",
                    width="small",
                    default="",
                ),
            },
        )
        st.session_state.EDITED_DF = edited_df

        output_file_name = st.text_input("Output file name", "SampleListPart_edited.sqx")
        st.download_button(
            label="Download `.sqx`",
            data=self._save_edits_and_get_zip(),
            file_name=output_file_name,
            mime="application/zip",
            help="Click to save and download..."
        )
        st.button('Reset & Upload New', type='primary', on_click=self._reset_state, use_container_width=True)
    def _reset_state(self) -> None:
        """
        """
        for key in st.session_state.keys():
            del st.session_state[key]
# --------------------------------------------------
if __name__ == "__main__":
    streamlit_app = App()
    streamlit_app._init_page()
