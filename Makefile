install:
	python setup.py install
package:
	python setup.py sdist
clean:
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
