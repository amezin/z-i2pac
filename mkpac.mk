z-i.pac: z-i/dump.csv z-i/nxdomain.txt mkpac.py
	./mkpac.py -o $@.tmp -p "$(PROXY)" -n z-i/nxdomain.txt z-i/dump.csv
	mv $@.tmp $@
