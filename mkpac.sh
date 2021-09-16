#!/usr/bin/env bash

set -ex

mkdir -p z-i

cd z-i

if [[ ! -e .git ]]; then
    git init
fi

Z_I_URL=https://github.com/zapret-info/z-i.git
PROXY="SOCKS5 192.168.1.1:1080"

if git remote | grep -Fx "origin"; then
    git remote set-url origin "${Z_I_URL}"
else
    git remote add origin "${Z_I_URL}"
fi

git fetch --depth 1 origin master
git checkout FETCH_HEAD

cd ..

./mkpac.py -o z-i.pac.tmp -p "${PROXY}" z-i/dump.csv
mv z-i.pac.tmp z-i.pac
