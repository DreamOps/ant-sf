#!/usr/bin/python
"""Renders a separate properties file for every row in a comma-separated file.
The directory for the properties files (property_dir) must exist.

To call from the Python CLI (with metadata present):
    % ./csv_to_properties.py -c incoming.csv -p outputdir

To call from the Ant CLI: ant -Dcsvfile_path=incoming.csv
                              -Dproperties_dir=outputdir
"""
"""
Use Case for csv_to_properties.py

Motivation: Supports mechanisms that run one build for each properties file in
a directory, such as the Jenkins Conditional Step plugin. The parameters can
be maintained in a spreadsheet, or other data source, and exported as CSV. To
support wildcard matching of row subsets, the files are named using multiple
columns from the spreadsheet,

Stakeholders: Release Engineering

Output: A set of properties files that can be used to launch a build with
the given set of parameters. The file is named for the first three columns
in the row in the format one.two.three.properties.

Prerequisites:
1. The parameters are available as a CSV file accessible to the build.
2. The first three columns of the spreadsheet can be concaternated into a
unique filename.
3. The properties_dir folder already exists.
4. A copy of this script is available to the build.

Postrequisites: None.

Success Scenario:
1. External actor invokes script from command line passing csvfile_path and
properties_dir arguments.
2. Script evaluates arguments and passes source and target arguments to main,
which orchestrates the process.
3. Process captures the column headers from the first row, and loops through
each other row in the CSV file.
4. For each row, a properties file is created, and each column in the row is
rendered as a property.

Alternate Scenarios:
1a Unexpected Parameters
1. External actor omits needed parameters.
2. System prints help text with proper usage.
3a Missing or incorrectly formatted inpout file.
1. Process is unable to open or parse the file.
2. System raises an input/output exception.
4a Invalid output folder
1. Process is unable to create or write to file.
2. System raises an input/output exception.

Enhancements:
1. Allow a variable number of columns to be passed as a parameter and used as
the filename, with an optional separator (rather than 1.2.3.properties).
2. Allow a variable number of columns to be passed to indicate which columns
are written to the propereties file.

"""
import argparse
import csv
from os import environ,path


LABEL_COL = 0
GROUP_COL = 1
PHASE_COL = 2
SEP = '='

# csvfile_path = 'org_data.csv'
# = 'org-data/'


def main(csvfile_path,properties_dir):

    with open(csvfile_path) as csvfile:
        reader = csv.DictReader(csvfile)
        fields = reader.fieldnames
        count = 0
        for row in reader:
            fn = '{label}.{group}.{phase}.properties'.format(
                label=row[fields[LABEL_COL]],
                group=row[fields[GROUP_COL]],
                phase=row[fields[PHASE_COL]])
            f = open(path.join(properties_dir, fn), 'w')
            for field in fields:
                f.write(field + SEP + row[field])
                f.write('\n')
            f.close()
            count += 1

        print "Extracted {} properties files from {} to {}.".format\
            (count, csvfile_path, properties_dir)


def __parser_config():
    parser = argparse.ArgumentParser(
        description="Renders a separate properties file for every row " \
                    "in a comma-separated file.",
        epilog="The parameters may also be passed as environment variables."
               "")
    parser.add_argument('-c', '--csvfile_path', help="The input file.")
    parser.add_argument('-p', '--properties_dir',
                        help="The storage folder for the properties files.")
    return parser


def __args_verify(csvfile_path,properties_dir):
    if csvfile_path is None or properties_dir is None:
        print "Requires csvfile_path, properties_dir as parameters or " \
              "system properties."
        exit(1)


if __name__ == '__main__':
    csvfile_path = None
    properties_dir = None

    try:
        csvfile_path = environ['csvfile_path']
        properties_dir = environ['properties_dir']
    except KeyError:
        pass

    parser = __parser_config()
    args = parser.parse_args()

    csvfile_path = args.csvfile_path if args.csvfile_path is not None else csvfile_path
    properties_dir = args.properties_dir if args.properties_dir is not None else properties_dir
    __args_verify(csvfile_path, properties_dir)

    main(csvfile_path, properties_dir)
