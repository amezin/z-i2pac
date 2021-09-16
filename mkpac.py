#!/usr/bin/env python3

import argparse
import csv
import ipaddress
import json
import logging
import sys
import urllib.parse


csv.field_size_limit(sys.maxsize)


def merge(addrs):
    addrs = sorted(addrs)
    if not addrs:
        return []

    merged = []

    def add_merged(addr):
        while merged:
            prev = merged[-1]
            if addr.subnet_of(prev):
                return

            addr_super = addr.supernet()
            if tuple(addr_super.subnets()) != (prev, addr):
                break

            addr = addr_super
            del merged[-1]

        merged.append(addr)

    for addr in addrs:
        add_merged(addr)

    return merged


def iter_field(field):
    for item in field.split('|'):
        item = item.strip()
        if item:
            yield item


def run(dump_csv, output, proxy):
    reader = csv.reader(dump_csv, delimiter=';')
    next(reader)  # "Updated on ..."

    addrs = set()
    domains = set()

    def add_addr(addr):
        try:
            ipaddr = ipaddress.ip_network(addr)

        except Exception:
            logging.exception("Can't parse %r as IP", addr)
            return

        if ipaddr.is_multicast:
            logging.warning('%r is multicast, ignoring', ipaddr)
            return

        if ipaddr.is_private:
            logging.warning('%r is private, ignoring', ipaddr)
            return

        if ipaddr.is_unspecified:
            logging.warning('%r is unspecified, ignoring', ipaddr)
            return

        if ipaddr.is_reserved:
            logging.warning('%r is reserved, ignoring', ipaddr)
            return

        if ipaddr.is_loopback:
            logging.warning('%r is loopback, ignoring', ipaddr)
            return

        if ipaddr.is_link_local:
            logging.warning('%r is link-local, ignoring', ipaddr)
            return

        addrs.add(ipaddr)

    for row in reader:
        for addr in iter_field(row[0]):
            add_addr(addr)

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

    logging.info('Total unique subnets: %d', len(addrs))

    merged_v4 = merge(addr for addr in addrs if addr.version == 4)
    merged_v6 = merge(addr for addr in addrs if addr.version == 6)

    logging.info('Merged subnets: %d', len(merged_v4) + len(merged_v6))
    logging.info('Total addresses: %d', sum(net.num_addresses for net in merged_v4) + sum(net.num_addresses for net in merged_v6))

    logging.info('Total domains: %d', len(domains))

    pac = f'''
function FindProxyForURL(url, host) {{
    const PROXY = {json.dumps(proxy)};
    const PROXY_DOMAINS = {json.dumps(list(domains), indent=4)};
    const IPV4_SUBNETS = {json.dumps(list([str(subnet.network_address), str(subnet.netmask)] for subnet in merged_v4), indent=4)};
    const resolved = dnsResolve(host);

    for (var i = 0; i < PROXY_DOMAINS.length; i++) {{
        if (dnsDomainIs(host, PROXY_DOMAINS[i])) {{
            return PROXY;
        }}
    }}

    for (var i = 0; i < IPV4_SUBNETS.length; i++) {{
        const [addr, mask] = IPV4_SUBNETS[i];
        if (isInNet(resolved, addr, mask)) {{
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