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

class App:
    def __init__(self):
        """
        """
    def _init_page(self) -> None:
        """
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

        if 'SAMPLES_LIST' not in st.session_state: self._init_file_uploader()
        else: self._update_plot()
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
        st.title('🧪 `sqx-editor`')
        st.markdown('These are a set of open-source tools to make handling electropherogram data easier.')
        st.markdown('Check out my GitHub with the link below for some of my other projects.')
        st.caption(f'[@{__author__}](https://github.com/ericksamera)\t|\tv{__version__}\t|\t{__comments__}')

        st.divider()

        return None
    
    def _init_file_management(self, input_file) -> None:
        """
        Function instantiates the temp dir for temporary storage of sequences
        and processes the uploaded/template file.
        """
        st.session_state.TEMP_DIR = pathlib.Path(__file__).parent.joinpath('temp')
        if st.session_state.TEMP_DIR.exists():
            shutil.rmtree(st.session_state.TEMP_DIR)
        st.session_state.TEMP_DIR.mkdir(parents=True, exist_ok=True)

        if input_file is not None:
            # Save the uploaded or template file temporarily
            zip_path = st.session_state.TEMP_DIR.joinpath(input_file.name)
            with open(zip_path, mode='wb') as temp_write:
                temp_write.write(input_file.read())

            # Extract the zip file
            extract_dir = st.session_state.TEMP_DIR.joinpath('extracted')
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            st.toast(f"File '{input_file.name}' processed successfully.", icon='😍')
            st.session_state.SAMPLES_LIST = self.parse_sample_list_part()


    def _init_file_uploader(self) -> None:
        """
        Initializes the file uploader, handles file uploads, and unzips files.
        """
        col1, col2 = st.columns(2)

        with col1:
            st.subheader('Upload sequence file (`.sqx`)')
            uploaded_file = st.file_uploader(
                'Upload `.zip` file containing sequences.',
                type=['sqx'],
                accept_multiple_files=False
            )

            if uploaded_file:
                st.button("Unzip File", on_click=self._init_file_management, args=(uploaded_file,))

        with col2:
            st.subheader("Create new sequence file")
            st.text("Use this option to create a new file.")
            st.button("Create from Template", on_click=self._create_from_template)


    def _write_new_sequence_to_xml(self) -> None:
        """
        Writes a new sequence to an XML file based on the current table data.
        """

        self._init_file_management()
        file_path = st.session_state.TEMP_DIR.joinpath('extracted/SampleListPart/SampleListPart')
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create a new XML structure
        root = ET.Element("SequenceTable", xmlns="http://schemas.datacontract.org/2004/07/Agilent.OpenLAB.Acquisition.AcquisitionMethodSequence")
        namespace = {'ns': "http://schemas.datacontract.org/2004/07/Agilent.OpenLAB.Acquisition.AcquisitionMethodSequence"}

        for sample in st.session_state.SAMPLES_LIST:
            entry = ET.SubElement(root, "anyType", attrib={"i:type": "SampleListEntry", "xmlns:i": "http://www.w3.org/2001/XMLSchema-instance"})
            ET.SubElement(entry, "SampleName").text = sample.sample_name
            ET.SubElement(entry, "SampleType").text = sample.sample_type
            ET.SubElement(entry, "AcquisitionMethod").text = sample.acquisition_method
            ET.SubElement(entry, "Vial").text = sample.vial
            ET.SubElement(entry, "Volume").text = sample.volume

        # Write the XML file
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)

        # Update the hash file
        self.update_sample_list_part_hash()
        st.success(f"New sequence written to {file_path} and hash updated.")
    def _init_new_sequence(self) -> None:
        """
        Initializes a new sequence table using a template XML file and allows editing.
        """
        # Path to the template file
        template_path = pathlib.Path(__file__).parent.joinpath("template.xml")
        if not template_path.exists():
            st.error("Template XML file not found.")
            return

        # Load the template XML
        tree = ET.parse(template_path)
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

        # Store the samples list and initialize the editor
        st.session_state.SAMPLES_LIST = samples
        st.success("New sequence table initialized from template.")
        self._update_plot()

    def _create_from_template(self) -> None:
        """
        Creates a new sequence table using the `template/HPLC1-2025-01-13 HPLC Training.sqx` file
        and processes it like an uploaded file.
        """
        # Path to the template file
        template_file_path = pathlib.Path(__file__).parent.joinpath("template/HPLC1-2025-01-13 HPLC Training.sqx")
        if not template_file_path.exists():
            st.error("Template `.sqx` file not found.")
            return

        # Read the template file as bytes
        with open(template_file_path, "rb") as f:
            file_bytes = f.read()

        # Mimic an uploaded file object
        template_file = io.BytesIO(file_bytes)
        template_file.name = template_file_path.name

        # Process the template file as if it were uploaded
        self._init_file_management(template_file)
        st.success("Sequence table created from template.")

    def parse_sample_list_part(self) -> list:
        """
        Parses the SampleListPart from the specified XML file in the temp directory.

        Returns:
            list: A list of SampleListEntry objects containing parsed sample information.
        """
        file_path = st.session_state.TEMP_DIR.joinpath('extracted').joinpath("SampleListPart/SampleListPart")
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Parse the XML file
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
        Converts a list of SampleListEntry objects to a list of dictionaries.

        Args:
            samples (list): List of SampleListEntry objects.

        Returns:
            list: List of dictionaries for use in a DataFrame.
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

    def _write_edits_to_xml(self) -> None:
        """
        Takes the edits from the DataFrame and writes them back to the XML file.
        """
        if "SAMPLES_LIST" not in st.session_state:
            st.error("No samples to save. Upload and edit a file first.")
            return

        # Retrieve the updated DataFrame from the editor
        edited_df = st.session_state.EDITED_DF

        # Path to the XML file
        file_path = st.session_state.TEMP_DIR.joinpath('extracted').joinpath("SampleListPart/SampleListPart")
        if not file_path.exists():
            st.error("SampleListPart XML file not found.")
            return

        # Load the existing XML
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespace = {'ns': "http://schemas.datacontract.org/2004/07/Agilent.OpenLAB.Acquisition.AcquisitionMethodSequence"}

        # Update XML entries based on the DataFrame
        for index, entry in enumerate(root.findall('ns:anyType', namespace)):
            if index < len(edited_df):
                entry.find('ns:SampleName', namespace).text = edited_df.loc[index, "sample-name"]
                entry.find('ns:SampleType', namespace).text = edited_df.loc[index, "sample-type"]
                entry.find('ns:AcquisitionMethod', namespace).text = edited_df.loc[index, "acq-method"]
                entry.find('ns:Vial', namespace).text = edited_df.loc[index, "vial"]
                entry.find('ns:Volume', namespace).text = str(edited_df.loc[index, "volume"])

        # Write the updated XML back to the file
        tree.write(file_path, encoding="utf-8", xml_declaration=True)
        st.success(f"Edits have been saved to {file_path}!")

    def create_zip_and_download(self):
        """
        Creates a zip file from the extracted directory structure and provides a download button in Streamlit.
        """
        temp_dir = st.session_state.TEMP_DIR.joinpath("extracted")

        if not temp_dir.exists():
            st.error("Extracted directory not found. Please upload and process a file first.")
            return

        # Create an in-memory zip file
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_dir.rglob("*"):
                # Write each file to the zip, preserving the relative structure
                relative_path = file_path.relative_to(temp_dir)
                zipf.write(file_path, arcname=relative_path)

        # Ensure the buffer's pointer is at the beginning
        zip_buffer.seek(0)

        # Add a download button for the zip file
        st.download_button(
            label="Download Edited Files as ZIP",
            data=zip_buffer,
            file_name="SampleListPart_edited.sqx",
            mime="application/zip",
            help="Click to download the updated files as a ZIP package."
        )
    def update_sample_list_part_hash(self) -> None:
        """
        Updates the `SampleListPart.chk` file with the SHA1 hash of the `SampleListPart` file.
        """
        # Paths to the files
        sample_list_path = st.session_state.TEMP_DIR.joinpath('extracted/SampleListPart/SampleListPart')
        hash_file_path = st.session_state.TEMP_DIR.joinpath('extracted/SampleListPart/SampleListPart.chk')

        if not sample_list_path.exists():
            st.error("SampleListPart file not found.")
            return

        # Read the contents of the SampleListPart file
        with open(sample_list_path, 'rb') as f:
            file_contents = f.read()

        # Compute the SHA1 hash
        sha1_hash = hashlib.sha1(file_contents).digest()

        # Write the hash to the .chk file
        with open(hash_file_path, 'wb') as f:
            f.write(sha1_hash)

        st.success(f"SHA1 hash updated in {hash_file_path}!")

    def _update_plot(self) -> None:
        """
        Updates the data editor plot with sample information and enables saving.
        """
        data_dicts = self._samples_to_dict(st.session_state.SAMPLES_LIST)
        data_df = pd.DataFrame(data_dicts)

        # Store the edited DataFrame in session state
        edited_df = st.data_editor(
            data_df,
            use_container_width=True,
            column_config={
                "check": st.column_config.CheckboxColumn(
                    " ",
                    default=False,
                    width="small",
                ),
                "vial": st.column_config.TextColumn(
                    "Vial",
                ),
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
            hide_index=True,
            num_rows="dynamic",
        )

        st.session_state.EDITED_DF = edited_df

        if st.button("Save Edits to XML", on_click=self._write_edits_to_xml):
            self.update_sample_list_part_hash()
        
        self.create_zip_and_download()
# --------------------------------------------------
if __name__=="__main__":
    streamlit_app = App()
    streamlit_app._init_page()