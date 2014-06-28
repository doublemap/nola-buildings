PYTHON=python

NOLA_Addresses_tulane_processed.osm: NOLA_Addresses_tulane.osm
	$(PYTHON) process_addresses.py < $< > $@
