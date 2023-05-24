import argparse

parser = argparse.ArgumentParser(
    description=""
    "This script is a simple tool I've thrown together to poke at the format of DCF files"
)
parser.add_argument(
    "dcf_filename",
    help="the dcf file to be parsed",
),
parser.add_argument(
    "row_type",
    nargs="?",
    help="filter to the given row type.  Default is all rows."
)
parser.add_argument(
    "col_numbers",
    nargs="*",
    default=[],
    help="filter to the given column.  Default is all columns."
),
parser.add_argument(
    "-v", "--verbose", help="record and print minor errors", action="store_true"
)
parser.add_argument(
    "-d",
    "--debug",
    help="Prints the names of sheets and fields as the script works",
    action="store_true",
)
args = parser.parse_args()
VERBOSE = args.verbose  # Controls whether or not checks for minor errors are run
DEBUG = args.debug      # If true, script will print its state in great detail as it runs
DCF_FILENAME = args.dcf_filename
ROW_TYPE = args.row_type
COL_NUMBERS = args.col_numbers


# Merges extra columns that were made when a comma was included in a quotation
def get_sanitized_row(line, row_number):
    sanitized_line = []
    while len(line) > 0:
        val = line.pop(0)
        if val == "":
            sanitized_line.append("")
            continue

        if val[0] == '"' and len(line) > 0:
            val += "," + line.pop(0)
            while val[-1] != '"' and len(line) > 0:
                val += "," + line.pop(0)

        if '"' in val and VERBOSE:
            print(f"{row_number}: {val}")

        sanitized_line.append(val)
    return sanitized_line


file = open(DCF_FILENAME)
lines = []
for line in file:
    if line and "," in line:
        lines.append(get_sanitized_row(line.split(","), len(lines)+1))
file.close()

print(DCF_FILENAME)

line_count = len(lines)
print(f"Line count: {line_count}")

print("Row Types:")
first_vals = {}
for line in lines:
    if line[0] not in first_vals:
        first_vals[line[0]] = 0
    first_vals[line[0]] += 1

values = list(first_vals.keys())
for val in values:
    print(f"    {val} - Occurs {first_vals[val]} times")

print("Column counts:")
col_counts = {}
for line in lines:
    line_type = line[0]
    if line_type not in col_counts.keys():
        col_counts[line_type] = {}
    if len(line) not in col_counts[line_type].keys():
        col_counts[line_type][len(line)] = 0
    col_counts[line_type][len(line)] += 1

for type in col_counts:
    print(f"    {type}:")
    counts = list(col_counts[type].keys())
    counts.sort()
    for count in counts:
        print(f"        {count} Columns occurs {col_counts[type][count]} times")


print("Looking for descents in ID sequence:")
highest = 0
ids = {}
for i in range(1, len(lines)):
    line = lines[i]
    id = int(line[1])

    if id not in ids:
        ids[id] = [0, []]
    ids[id][0] += 1
    ids[id][1] = i

    if id > highest:
        highest = id
        continue

    if id < highest:
        print(f"    Row {i} - ID value lowered from {highest} to {id}!")

print("Looking for duplicate ID's:")
for id in ids.keys():
    count, rows = ids[id]
    if count > 1:
        print(f"    Duplicate found - ID {id} found on rows {str(rows)}")

if ROW_TYPE != None:
    print(f"Looking for rows beginning with {ROW_TYPE} - Columns {','.join(COL_NUMBERS)}")
    for i in range(len(lines)):
        line = lines[i]
        row_type = line[0]
        if row_type != ROW_TYPE:
            continue

        columns = []
        if len(COL_NUMBERS) == 0:
            columns = line
        else:
            for c in range(len(line)):
                if str(c) in COL_NUMBERS:
                    columns.append(line[c])

        for val in columns:
            if val != "":
                print(f"    {i}: {line[0]} ({len(line)} Columns) - {', '.join(columns)}")
                break