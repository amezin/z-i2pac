include defaults.mk

z-i.pac: z-i/dump.csv z-i/nxdomain.txt mkpac.py $(MAKEFILE_LIST)
	./mkpac.py -o $@.tmp -p "$(PROXY)" -n z-i/nxdomain.txt z-i/dump.csv
	mv $@.tmp $@
