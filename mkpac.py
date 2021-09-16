#!/usr/bin/env python3

import argparse
import csv
import json
import logging
import sys
import urllib.parse


csv.field_size_limit(sys.maxsize)


def iter_field(field):
    for item in field.split('|'):
        item = item.strip()
        if item:
            yield item


def run(dump_csv, output, proxy):
    reader = csv.reader(dump_csv, delimiter=';')
    next(reader)  # "Updated on ..."

    domains = set()

    for line_number, row in enumerate(reader, start=2):
        for domain in iter_field(row[1]):
            if domain.startswith('*.'):
                domain = domain[2:]

            if domain.startswith('.'):
                domain = domain[1:]

            if domain:
                domains.add(domain)
            else:
                logging.warning("Empty domain name in line %d", line_number)

        for url in iter_field(row[2]):
            try:
                domain = urllib.parse.urlsplit(url, scheme='http').hostname
                if domain:
                    domains.add(domain)
                else:
                    logging.warning("Can't find hostname in %r URL, line %d", url, line_number)

            except Exception:
                logging.exception("Can't parse %r as URL, line %d", url, line_number)

    logging.info('Total domains: %d', len(domains))

    pac = f'''
function FindProxyForURL(url, host) {{
    const PROXY = {json.dumps(proxy)};
    const PROXY_DOMAINS = {json.dumps(list(domains), indent=4)};

    for (var i = 0; i < PROXY_DOMAINS.length; i++) {{
        if (dnsDomainIs(host, PROXY_DOMAINS[i])) {{
            return PROXY;
        }}
    }}

    return "DIRECT";
}}'''

    print(pac.strip(), file=output)
    output.close()


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('dump_csv', type=argparse.FileType('r', encoding='cp1251'))
    parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-p', '--proxy', type=str, required=True)
    run(**vars(parser.parse_args()))


if __name__ == '__main__':
    main()