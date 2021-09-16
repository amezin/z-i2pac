#!/usr/bin/env bash

PROXY="${1:-SOCKS5 192.168.1.1:1080}"

set -ex

[ "$(pactester -p z-i.pac -u 'http://rutracker.org')" == "${PROXY}" ]

[ "$(pactester -p z-i.pac -u 'http://www.rutracker.org')" == "${PROXY}" ]

[ "$(pactester -p z-i.pac -u 'http://www.google.com')" == "DIRECT" ]

[ "$(pactester -p z-i.pac -u 'http://195.82.146.214')" == "${PROXY}" ]

[ "$(pactester -p z-i.pac -u 'http://8.8.8.8" == "DIRECT" ]
