.PHONY: data image
data:
	pip install -r requirements-build.txt
	./manage.py migrate
	./manage.py load_geonames
	./manage.py load_asciified_geonames

image:
	packer build -only=openstack packer.json
