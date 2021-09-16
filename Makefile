#!/usr/bin/make -f

Z_I_URL := https://github.com/zapret-info/z-i.git
PROXY := SOCKS5 192.168.1.1:1080

all: z-i.pac

.PHONY: all

z-i:
	mkdir -p $@

z-i/.git: | z-i
	cd $(@D) && git init
	cd $(@D) && git remote add origin $(Z_I_URL)

z-i/update: z-i/.git
	cd $(@D) && git remote set-url origin $(Z_I_URL)
	cd $(@D) && git fetch --depth 1 origin master
	cd $(@D) && git checkout FETCH_HEAD

.PHONY: z-i/update

ifeq ($(RECURSE),)

z-i.pac: z-i/update
	$(MAKE) RECURSE=1 $@

else

z-i.pac: z-i/dump.csv mkpac.py
	./mkpac.py -o $@.tmp -p "$(PROXY)" $<
	mv $@.tmp $@

endif

test: z-i.pac
	./test.sh "$(PROXY)"

.PHONY: test
