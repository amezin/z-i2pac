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

    for row in reader:
        for domain in iter_field(row[1]):
            if domain.startswith('*.'):
                domain = domain[2:]

            if domain:
                domains.add(domain)

        for url in iter_field(row[2]):
            try:
                domain = urllib.parse.urlsplit(url, scheme='http').hostname
                if domain:
                    domains.add(domain)

            except Exception:
                logging.exception("Can't parse %r as URL", url)

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