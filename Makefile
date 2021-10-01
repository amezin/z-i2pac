#!/usr/bin/make -f

Z_I_URL := https://github.com/zapret-info/z-i.git
PROXY := SOCKS5 192.168.1.1:1080

ifeq ($(guile (string-downcase "$(firstword $(PROXY))")),PROXY)
	GIT_PROXY := $(wordlist 2,$(words $(PROXY)),$(PROXY))
else
	GIT_PROXY := $(guile (string-downcase "$(firstword $(PROXY))"))://$(wordlist 2,$(words $(PROXY)),$(PROXY))
endif

all: z-i.pac

.PHONY: all

z-i:
	mkdir -p $@

z-i/.git: | z-i
	cd $(@D) && git init
	cd $(@D) && git remote add origin $(Z_I_URL)

z-i/update: z-i/.git
	cd $(@D) && git remote set-url origin $(Z_I_URL)
	cd $(@D) && git -c "http.proxy=$(GIT_PROXY)" -c "https.proxy=$(GIT_PROXY)" fetch --depth 1 origin master
	cd $(@D) && git checkout FETCH_HEAD

.PHONY: z-i/update

z-i.pac: z-i/update
	$(MAKE) -f mkpac.mk "PROXY=$(PROXY)" $@

.PHONY: z-i.pac

test: z-i.pac
	./test.sh "$(PROXY)"

.PHONY: test
