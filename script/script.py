import csv
import re

def parse_data(input_file_path, output_file_path):
    """
    Parses a custom binary/text format file, extracts structured data,
    and writes it to a CSV file. 
    The input file uses null characters ('\\x00') as delimiters. Each record
    starts with a numeric serial number. The number of fields per record is variable.

    Args:
        input_file_path (str): The path to the input data file.
        output_file_path (str): The path where the output CSV will be saved.
    """
    # --- Step 1: File Inspection and Analysis ---
    # The file is read in binary mode to correctly handle null bytes and varied encoding.
    try:
        with open(input_file_path, 'rb') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_file_path}'")
        return

    # --- Step 2: Parsing and Record Extraction ---
    # The content is split by the null delimiter. We decode using 'latin-1' because
    # it can represent every possible byte, preventing errors with mixed text/binary data.
    # Empty fields resulting from the split are filtered out.
    fields = content.split(b'\\x00')   # split by null byte
    all_fields = []                   # make an empty list

    for field in fields:
        if field:  # skip empty parts
            text = field.decode('latin-1')  # convert bytes → string
            text = text.strip()             # remove spaces/newlines
            all_fields.append(text)         # add to the list

    # Records are identified by a numeric "Serial Number". We find the start index of each record.
    # The check is now more specific: a short, purely numeric field. This prevents long
    # numeric fields (like Reference Numbers) from being incorrectly marked as a new record start.
    start_indices = []

    # Use enumerate() to get both the index (i) and the value (field) for each item.
    for i, field in enumerate(all_fields):
        
        # This is the same condition as in the list comprehension.
        # It checks if the field is a number AND is short.
        if field.isdigit() and len(field) < 4:
            
            # If the conditions are met, add the index 'i' to our list.
            start_indices.append(i)
        
    records_data = []
    for i in range(len(start_indices)):
        start = start_indices[i]
        # The end of a chunk is the start of the next one, or the end of the file.
        end = start_indices[i + 1] if i + 1 < len(start_indices) else len(all_fields)
        chunk = all_fields[start:end]
        if chunk:
            records_data.append(process_chunk(chunk))

    # --- Step 5: Generating the CSV Output ---
    write_to_csv(records_data, output_file_path)
    print(f"Successfully parsed data and created '{output_file_path}'")

def process_chunk(chunk):
    """
    Processes a single record's data (a "chunk") and maps its fields to the
    defined CSV columns using pattern matching and positional logic.

    Args:
        chunk (list): A list of strings representing one record, starting with a serial number.

    Returns:
        dict: A dictionary with keys matching the CSV headers and values from the chunk.
    """
    # --- Step 3: Field Mapping and Logic ---
    headers = [
        "Serial Number", "Part Number", "Part Name English", 
        "Part Name Language 1", "Part Name Language 2", "Part Name Language 3", 
        "Part Name Language 4", "Part Name Language 5", 
        "Part Number in Other Format", "Reference Number", 
        "Additional Information", "Extra Data"
    ]
    record = {h: '' for h in headers}
    
    # The first item in a chunk is always the Serial Number.
    record['Serial Number'] = chunk[0]
    data_fields = chunk[1:]

    # Handle empty records (like #22, #24)
    if not data_fields:
        return record

    # Regex to identify part numbers with dots (e.g., "X530.108.146.000")
    # and reference numbers (e.g., "72311106").
    part_num_other_format_regex = re.compile(r'^[A-Z0-9\.]+$') # Contains only uppercase letters, digits, and dots.
                                                                # Has at least one character
                                                                # No spaces, no lowercase letters, no other symbols
    ref_num_regex = re.compile(r'^[0-9]{8,}$') # Reference numbers are typically long
                                                # Contains only digits (0–9)
                                                # Has a minimum length of 8 digits
                                                # No letters, no spaces, no symbols

    # The first field is usually the Part Number, but not always (e.g., record #20).
    # We will tentatively assign it and correct it later if needed.
    current_pos = 0
    if current_pos < len(data_fields):
        record['Part Number'] = data_fields[current_pos]
        current_pos += 1

    # Consume all name/description fields. The sequence of names ends when we encounter
    # a field that strongly matches the pattern of a formatted part number or a reference number.
    names_end_pos = current_pos
    for i in range(current_pos, len(data_fields)):
        field = data_fields[i]
        is_formatted_part_num = bool(part_num_other_format_regex.match(field) and '.' in field)
        is_ref_num = bool(ref_num_regex.match(field))
        
        # This condition marks the end of the variable-length name fields.
        if is_formatted_part_num or is_ref_num:
            break
        names_end_pos += 1
    
    names = data_fields[current_pos:names_end_pos]
    
    # Handle special case for record #20 which has no part number.
    if record['Serial Number'] == '20':
        names.insert(0, record['Part Number']) # The tentative part number was actually the first name.
        record['Part Number'] = ''
        
        # Custom mapping for record #20. There is a mess with part names and languages.
        # We will assign names based on a predefined mapping.
        mapping = {
            0: "Part Name Language 2",
            1: "Part Name English",
            2: "Part Name Language 4",
            3: "Part Name Language 1",
            4: "Part Name Language 3",
            5: "Part Name Language 5",
        }
        
    # Assign the collected names to the appropriate columns.
    name_headers = headers[2:8] # "Part Name English" through "Part Name Language 5"
    for i, name in enumerate(names):
        if record['Serial Number'] == '20':
            if i in mapping: # Use custom mapping for record #20
                record[mapping[i]] = name
        else:
            if i < len(name_headers):
                record[name_headers[i]] = name
            
    current_pos = names_end_pos

    # Sequentially assign the next fields based on their patterns.
    # Part Number in Other Format
    if current_pos < len(data_fields) and part_num_other_format_regex.match(data_fields[current_pos]) and '.' in data_fields[current_pos]:
        record['Part Number in Other Format'] = data_fields[current_pos]
        current_pos += 1
    
    # Reference Number
    if current_pos < len(data_fields) and ref_num_regex.match(data_fields[current_pos]):
        record['Reference Number'] = data_fields[current_pos]
        current_pos += 1
        
    # Additional Information is the single next field, if it exists.
    if current_pos < len(data_fields):
        record['Additional Information'] = data_fields[current_pos]
        current_pos += 1

    # --- Step 4: Handling Extra Data ---
    
    # Special case: Delete "white noise" from position 61. 
    # These data have no sense and most probably are distractor
    if record['Serial Number'] == '61':
        data_fields[current_pos:] = []
    
    # Any remaining fields are considered "Extra Data" and are joined with '___'.
    extra_data = data_fields[current_pos:]
    if extra_data:
        record['Extra Data'] = '___'.join(extra_data)
    else:
        record['Extra Data'] = '-' # Use a placeholder if no extra data exists.
        
    return record

def write_to_csv(records, file_path):
    """Writes a list of record dictionaries to a CSV file."""
    if not records:
        print("No records to write.")
        return
        
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)