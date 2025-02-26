install:
	poetry install

.PHONY: test

test:
	odmt --nolayers --input ~/github/molteno/physics/disko_array_opt/ispiral_24/ispiral_24_bottom.dxf --output test.dxf
