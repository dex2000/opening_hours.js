#!/usr/bin/env python3
# encoding: utf-8
# @license AGPLv3 <https://www.gnu.org/licenses/agpl-3.0.html>
# @author Copyright (C) 2015 Robin Schneider <ypid@riseup.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3 of the
# License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Merge all stats into a country wide statistic.
"""

__version__ = '0.9'

# modules {{{
# std {{{
import logging
import csv
# }}}
# }}}


class CsvMerge:
    CSV_FIELDNAMES = (
        'Time',
        'Number of values',
        'Number of different values',
        'Number of values which could be parsed',
        'Number of different values which could be parsed',
        'Number of values which returned a warning',
        'Number of different values which returned a warning',
        'Number of values which are not prettified',
        'Number of different values which are not prettified',
    )

    def __init__(
        self,
        csv_files,
    ):

        self._merged_data = {}
        self._merged_data_sources = {}
        self._csv_files = csv_files
        self._data_sources_count = len(self._csv_files)

        for self._csv_file in self._csv_files:
            self.parse_file()

    def parse_file(self):
        logger.info(u"Parsing file: {}".format(self._csv_file))

        self._csv_fh = open(self._csv_file, newline='')

        sample = self._csv_fh.read(1024)
        if not csv.Sniffer().has_header(sample):
            raise Exception("No header line in CSV file found. This seems to be not a file generated by real_test.js.")
        self._csv_fh.seek(0)  # rewind

        # FIXME might use sniffer for delimiter detection.
        # logger.debug(csv.Sniffer().sniff(sample))
        if sample.find(','):
            self._csv_delimiter = ','
        elif sample.find(';'):
            self._csv_delimiter = ';'
        else:
            raise Exception("Unknown CSV delimiter.")

        self._parse()

    def _parse(self):
        for self.__row in csv.DictReader(
            filter(lambda row: row[0] != '#', self._csv_fh),
            skipinitialspace=True,
            delimiter=self._csv_delimiter
        ):

            self._parse_row()

    def _parse_row(self):
        # logger.debug("Parsing row: \"{0}\"".format(self.__row))

        self._merged_data.setdefault(self.__row['Time'], {})
        self._merged_data_sources.setdefault(self.__row['Time'], set([]))
        self._merged_data_sources[self.__row['Time']].add(self._csv_file)
        for key in self.CSV_FIELDNAMES:
            self._merged_data[self.__row['Time']].setdefault(key, 0)
            if key == 'Time':
                self._merged_data[self.__row['Time']][key] = self.__row[key]
            else:
                self._merged_data[self.__row['Time']][key] += int(self.__row[key])

    def write_combined_csv(self, filename):

        file_fh = open(filename, 'w')
        writer = csv.DictWriter(file_fh, self.CSV_FIELDNAMES, restval=' ')
        writer.writeheader()

        for time in sorted(self._merged_data):
            available_sources = len(self._merged_data_sources[time])
            if self._data_sources_count == available_sources:
                writer.writerow(self._merged_data[time])
                # logger.debug(self._merged_data[time])
            elif logger.getEffectiveLevel() == logging.DEBUG:
                missing_csv_files = []
                for csv_file in self._csv_files:
                    if csv_file not in self._merged_data_sources[time]:
                        missing_csv_files.append(csv_file)
                if len(missing_csv_files):
                    logger.debug(
                        u"Missing files for {}: {}".format(
                            time,
                            missing_csv_files,
                        )
                        # + u" (present: {})".format(self._merged_data_sources[time])
                    )


# main {{{
if __name__ == '__main__':
    from argparse import ArgumentParser

    args_parser = ArgumentParser(
        description=__doc__,
    )
    args_parser.add_argument(
        '-V', '--version',
        action='version',
        version='%(prog)s {version}'.format(version=__version__),
    )
    args_parser.add_argument(
        '-d', '--debug',
        help="Print lots of debugging statements",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.WARNING,
    )
    args_parser.add_argument(
        '-v', '--verbose',
        help="Be verbose",
        action="store_const", dest="loglevel", const=logging.INFO,
    )
    args_parser.add_argument(
        'csv_files',
        help=u"CSV host list file to import.",
        nargs="+",
    )
    args_parser.add_argument(
        '-o', '--output-file',
        help="Output country wide CSV file.",
        required=True,
    )

    args = args_parser.parse_args()
    logger = logging.getLogger(__file__)
    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        level=args.loglevel,
        # level=logging.DEBUG,
        # level=logging.INFO,
    )

    merger = CsvMerge(
        args.csv_files,
    )

    merger.write_combined_csv(args.output_file)

# }}}
