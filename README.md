# Data-Parcing

## Overview

**Data-Parcing** is a Python project for parsing custom binary/text data files and extracting structured records into CSV format. It is designed to process files with null-byte delimiters and variable record structures, making it suitable for technical, engineering, or catalog data sources.

## Features
- Parses files with null-byte (`\x00`) delimiters
- Extracts records based on serial numbers
- Handles variable-length fields and multilingual part names
- Outputs structured data to CSV
- Includes a Jupyter notebook for interactive exploration

## File Structure
```
Data-Parcing/
├── main.py                  # Entry point for parsing
├── script/
│   └── script.py            # Core parsing logic
├── source_data/
│   └── Input_File_01.txt    # Example input data file
├── output_data/
│   └── output.csv           # Example output CSV
├── data_parcing_notebook.ipynb # Jupyter notebook for analysis
├── requirements.txt         # Python dependencies
├── LICENSE                  # License file
└── README.md                # Project documentation
```

## Usage
Before starting ot use the parser, ensure that you created source_data directory and placed your input file `Input_File_01.txt` there.

### 1. Run the Parser
To parse the example input file and generate a CSV:
```bash
python main.py
```
This reads `source_data/Input_File_01.txt` and writes results to `output_data/output.csv`.

### 2. Jupyter Notebook
Open `data_parcing_notebook.ipynb` for step-by-step data inspection and parsing in an interactive environment.

## How It Works
- The parser reads the input file in binary mode to handle null bytes and mixed encodings.
- The content is split by the null delimiter. We decode using 'latin-1' because it can represent every possible byte, preventing errors with mixed text/binary data. Empty fields resulting from the split are filtered out.
- Records are identified by a numeric "Serial Number". We find the start index of each record. The check is now more specific: `if field.isdigit() and len(field) < 4`. This prevents long numeric fields (like Reference Numbers) from being incorrectly marked as a new record start.
- The fields between two serial numbers are grouped as one chunk (record).Each chunk is proceed separatly in `process_chunk()` function. It maps its fields to the defined CSV columns using pattern matching and positional logic. It returns a dictionary with keys matching the CSV headers and values from the chunk.
- `process_chunk()` logic:
    - Some recorrds (#22, #23) are empty. The parser skips these to ensure only valid data is included in the output.
    - Regex patterns are used to identify part numbers in other formats and reference numbers:
        - Part numbers in other formats may include uppercase letters, digits, and dots (e.g., "X530.108.146.000").
        - Reference numbers are typically long numeric strings (more then 8 characters).
    - The first field is usually the Part Number, but not always (e.g., record #20). On this stage the first fields are tentatively assigned as Part Numbers for all chunks, later they will be corrected if necessary.
    - Then a list of names in different languages is built. The sequence of names ends when we encounter a field that strongly matches the pattern of a formatted part number or a reference number. So we include into the lisr of names everything that lays between the part number and the first field that matches either the part number or the reference number pattern.
    - On the next step special case for record #20 which has no part number is handled. The tentative part number was actually the first name.
    - The collected names are assigned to the appropriate columns.
    - Using the regex paterns defined earlier the actual part number and reference number are identified and assigned to their respective columns.
    - Additional information as a next field (if it exists) after the reference number is assigned to the "Additional Unformation" column.
    - In case of record #61, which contains irrelevant "white noise" data, this field is removed to avoid cluttering the output.
    - Finally, any remaining fields are considered "Extra Data" and are joined with '___'. If no extra data exists, placeholder '-' is used.
- At the end, all processed records are written to a CSV file with appropriate headers.

The whole process can be summarized in the following flowchart:
```mermaid
flowchart TD
    A[Read input file in binary mode] --> B[Split content by null delimiter (\x00)]
    B --> C[Decode fields using 'latin-1' and filter empty fields]
    C --> D[Identify record start by short numeric Serial Number]
    D --> E[Group fields between serial numbers as one chunk (record)]
    E --> F[Process each chunk in process_chunk()]
    F --> G[Skip empty records (#22, #23)]
    F --> H[Assign tentative Part Number (first field)]
    H --> I[Build list of names in different languages]
    I --> J[Handle special case for record #20 (no part number)]
    J --> K[Assign names to appropriate columns]
    K --> L[Identify and assign Part Number in Other Format and Reference Number using regex]
    L --> M[Assign Additional Information (if exists)]
    M --> N[Remove irrelevant data for record #61]
    N --> O[Join remaining fields as Extra Data or use '-' if none]
    O --> P[Write all processed records to CSV with headers]
```

## Requirements
Build a Python development container with the necessary dependencies listed in `requirements.txt`.

## Example Output
See `output_data/output.csv` for a sample of the parsed data.

## License
This project is licensed under the terms of the LICENSE file in this repository.

## Author
Created by Mykola Senko
September 20, 2025
Kortrijk, Belgium