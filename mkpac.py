#!/usr/bin/env python3

import argparse
import collections.abc
import csv
import enum
import itertools
import json
import logging
import sys
import urllib.parse


csv.field_size_limit(sys.maxsize)


def iter_field(field):
    for item in field.split(' | '):
        item = item.strip()
        if item:
            yield item


@enum.unique
class Column(enum.IntEnum):
    IPS = 0
    DOMAINS = 1
    URLS = 2


def parse_domain(domain):
    if domain.startswith('*.'):
        domain = domain[2:]

    if domain.startswith('.'):
        domain = domain[1:]

    return tuple(part for part in reversed(domain.split('.')) if part)


def unparse_domain(domain):
    if len(domain) == 1:
        return f'.{domain[0]}'

    return '.'.join(reversed(domain))


def parent_domains(parsed_domain):
    for level in range(1, len(parsed_domain)):
        yield parsed_domain[:level]


INDENT = '\t'


HEADER = f'''
function DnsDomainInList(domain, domainList) {{
{INDENT}for (var i = 0; i < domainList.length; i++) {{
{INDENT * 2}if (dnsDomainIs(domain, domainList[i])) return true;
{INDENT}}}
{INDENT}return false;
}}
'''


def run(dump_csv, output, proxy, nxdomain):
    if nxdomain:
        nx_domains = set(parse_domain(line.strip()) for line in nxdomain)
    else:
        nx_domains = set()

    domains = set()

    def add_domain(domain):
        parsed_domain = parse_domain(domain)

        if not parsed_domain:
            return

        if parsed_domain in nx_domains:
            return

        if any((parent_domain in nx_domains) for parent_domain in parent_domains(parsed_domain)):
            return

        if all(part.isdecimal() for part in parsed_domain):
            return

        domains.add(parsed_domain)

    reader = csv.reader(dump_csv, delimiter=';')
    next(reader)  # Skip "Updated on ..."

    for line_number, row in enumerate(reader, start=2):
        for domain in iter_field(row[Column.DOMAINS]):
            if domain:
                add_domain(domain)
            else:
                logging.warning("Empty domain name in line %d", line_number)

        for url in iter_field(row[Column.URLS]):
            try:
                domain = urllib.parse.urlsplit(url, scheme='http').hostname
                if domain:
                    add_domain(domain)
                else:
                    logging.warning("Can't find hostname in %r URL, line %d", url, line_number)

            except Exception:
                logging.exception("Can't parse %r as URL, line %d", url, line_number)

    logging.info('Total domains: %d', len(domains))

    def gen(parent_domain, domains):
        groups = {}

        for k, g in itertools.groupby(domains, key=lambda domain: domain[:len(parent_domain) + 1]):
            if k == parent_domain:
                return k

            groups[k] = gen(k, g)

        if len(groups) == 1:
            return next(iter(groups.values()))

        return groups

    print(HEADER, file=output)

    func_counter = 0

    def gencode(groups):
        nonlocal func_counter
        func_name = f'Match{func_counter}'
        func_counter += 1

        simple_yes = []
        call_other = []

        for k, g in groups.items():
            if isinstance(g, collections.abc.Mapping):
                call_other.append((unparse_domain(k), gencode(g)))
            else:
                simple_yes.append(unparse_domain(k))

        print(f'function {func_name}(domain) {{', file=output)

        if simple_yes:
            print(f'{INDENT}const SIMPLE_YES =', file=output, end='')
            json.dump(simple_yes, output, indent=INDENT * 2)
            print(';', file=output)
            print(f'{INDENT}if (DnsDomainInList(domain, SIMPLE_YES)) return true;', file=output)

        for domain, func in call_other:
            print(f'{INDENT}if (dnsDomainIs(domain, {json.dumps(domain)})) return {func}(domain);', file=output)

        print(f'{INDENT}return false;', file=output)
        print(f'}}', file=output)
        print('', file=output)
        return func_name

    main_match = gencode(gen(tuple(), sorted(domains)))

    print('function FindProxyForURL(url, host) {', file=output)
    print(f'{INDENT}if ({main_match}(host)) return {json.dumps(proxy)};', file=output)
    print(f'{INDENT}return "DIRECT";', file=output)
    print('}', file=output)

    output.close()


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('dump_csv', type=argparse.FileType('r', encoding='cp1251'))
    parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-p', '--proxy', type=str, required=True)
    parser.add_argument('-n', '--nxdomain', type=argparse.FileType('r', encoding='cp1251'))
    run(**vars(parser.parse_args()))


if __name__ == '__main__':
    main()