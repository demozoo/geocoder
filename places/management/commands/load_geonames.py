from django.conf import settings
from django.core.management.base import BaseCommand

from contextlib import contextmanager
from urllib.request import urlretrieve
import os.path
from zipfile import ZipFile
from io import StringIO

from ...models import Country, Admin1Code, Admin2Code, Locality, AlternateName


class Command(BaseCommand):
	data_dir = os.path.join(settings.BASE_DIR, 'data')

	countries = {}
	localities = set()

	def ensure_local_file(self, url):
		filename = url.split('/')[-1]
		path = os.path.join(self.data_dir, filename)

		if not os.path.exists(path):
			urlretrieve(url, path)

		return path

	@contextmanager
	def open_file(self, url):
		path = self.ensure_local_file(url)

		fd = open(path, 'r')
		yield fd
		fd.close()

	def clear_tables(self):
		print("Clearing tables")
		from django.db import connection
		cursor = connection.cursor()
		for model in (AlternateName, Locality, Admin2Code, Admin1Code, Country):
			cursor.execute('DELETE FROM {0}'.format(model._meta.db_table))

	def load_countries(self):
		objects = []
		with self.open_file('http://download.geonames.org/export/dump/countryInfo.txt') as fd:
			print("Importing countries")
			for line in fd:
				if line.startswith('#'):
					continue

				fields = line.split('\t')
				iso, iso3, iso_numeric, fips, name, capital, area, population, continent, tld, currency_code, currency_name, phone, postcode_format, postcode_regex, languages, geonameid = fields[:17]
				if geonameid == '':  # former countries Serbia and Montenegro and Netherlands Antilles are present in countryInfo.txt with no geonames code
					continue

				self.countries[iso] = {}

				objects.append(Country(code=iso, name=name, geonameid=geonameid))
		Country.objects.bulk_create(objects)

	def load_admin1_codes(self):
		objects = []
		with self.open_file('http://download.geonames.org/export/dump/admin1CodesASCII.txt') as fd:
			print("Importing admin level 1 codes")
			for line in fd:
				fields = line[:-1].split('\t')
				codes, name = fields[0:2]
				country_code, admin1_code = codes.split('.')
				geonameid = fields[3]
				self.countries[country_code][admin1_code] = {'geonameid': geonameid, 'admins2': {}}
				objects.append(Admin1Code(geonameid=geonameid,
					code=admin1_code,
					name=name,
					country_id=country_code))
		Admin1Code.objects.bulk_create(objects)

	def load_admin2_codes(self):
		objects = []
		admin2_set = set()  # to find duplicated
		skipped_duplicated = 0
		with self.open_file('http://download.geonames.org/export/dump/admin2Codes.txt') as fd:
			print("Importing admin level 2 codes")
			for line in fd:
				fields = line[:-1].split('\t')
				codes, name = fields[0:2]
				country_code, admin1_code, admin2_code = codes.split('.')

				# if there is a duplicated
				long_code = "{0}.{1}.{2}".format(country_code, admin1_code, name)
				if long_code in admin2_set:
					skipped_duplicated += 1
					continue

				admin2_set.add(long_code)

				geonameid = fields[3]
				admin1_dic = self.countries[country_code].get(admin1_code)

				# if there is not admin1 level we save it but we don't keep it for the localities
				if admin1_dic is None:
					admin1_id = None
				else:
					# If not, we get the id of admin1 and we save geonameid for filling in Localities later
					admin1_id = admin1_dic['geonameid']
					admin1_dic['admins2'][admin2_code] = geonameid

				objects.append(
					Admin2Code(geonameid=geonameid, code=admin2_code, name=name,
						country_id=country_code, admin1_id=admin1_id)
				)

		Admin2Code.objects.bulk_create(objects)
		print('{0:8d} Admin2Codes loaded'.format(Admin2Code.objects.all().count()))
		print('{0:8d} Admin2Codes skipped because duplicated'.format(skipped_duplicated))

	def load_localities(self):
		print('Loading localities')
		objects = []
		batch = 100
		processed = 0
		batches_done = 0
		zip_path = self.ensure_local_file('http://download.geonames.org/export/dump/allCountries.zip')

		all_countries_zip = ZipFile(zip_path)
		all_countries_txt = all_countries_zip.open('allCountries.txt')
		for line in all_countries_txt:
			line = line.decode('utf-8')
			fields = line.split('\t')
			geonameid, name, asciiname, altnames, lat, lng, feature_class, feature_code, country_code, cc2, admin1_code, admin2_code, admin3_code, admin4_code, population = fields[:15]
			if feature_class not in ('P', 'A'):
				continue
			if country_code:
				try:
					admin1_dic = self.countries[country_code].get(admin1_code)
				except KeyError:  # someone's probably left in an entry for a non-existent country like Serbia and Montenegro. Whoopee.
					continue

				if admin1_dic:
					admin1_id = admin1_dic['geonameid']
					admin2_id = admin1_dic['admins2'].get(admin2_code)
				else:
					admin1_id = None
					admin2_id = None
			else:
				country_code = None
				admin1_id = None
				admin2_id = None

			if population:
				population = int(population)
			else:
				population = None

			locality = Locality(
				geonameid=geonameid,
				name=name,
				country_id=country_code,
				admin1_id=admin1_id,
				admin2_id=admin2_id,
				latitude=lat,
				longitude=lng,
				feature_class=feature_class,
				feature_code=feature_code,
				population=population)
			objects.append(locality)
			processed += 1
			self.localities.add(geonameid)

			if processed % batch == 0:
				Locality.objects.bulk_create(objects)
				print("{0:8d} Localities loaded".format(processed))
				objects = []

				batches_done += 1
				if batches_done % 100 == 0:
					print("reopening db connection...")
					from django.db import close_old_connections
					close_old_connections()

		all_countries_zip.close()

		Locality.objects.bulk_create(objects)
		print("{0:8d} Localities loaded".format(processed))

	def load_altnames(self):
		print('Loading alternate names')
		objects = []
		allobjects = {}
		batch = 100
		processed = 0
		batches_done = 0
		zip_path = self.ensure_local_file('http://download.geonames.org/export/dump/alternateNames.zip')

		alternate_names_zip = ZipFile(zip_path)
		alternate_names_txt = alternate_names_zip.open('alternateNames.txt')
		for line in alternate_names_txt:
			line = line.decode('utf-8')
			fields = line.split('\t')
			locality_geonameid = fields[1]
			if locality_geonameid not in self.localities:
				continue

			if fields[2] == 'link':
				continue

			name = fields[3]
			is_preferred_name = bool(fields[4])
			is_short_name = bool(fields[5])
			if locality_geonameid in allobjects:
				if name in allobjects[locality_geonameid]:
					continue
			else:
				allobjects[locality_geonameid] = set()

			allobjects[locality_geonameid].add(name)
			objects.append(AlternateName(
				locality_id=locality_geonameid,
				name=name,
				is_preferred_name=is_preferred_name,
				is_short_name=is_short_name))
			processed += 1

			if processed % batch == 0:
				AlternateName.objects.bulk_create(objects)
				print("{0:8d} AlternateNames loaded".format(processed))
				objects = []

				batches_done += 1
				if batches_done % 100 == 0:
					print("reopening db connection...")
					from django.db import close_old_connections
					close_old_connections()

		alternate_names_zip.close()

		AlternateName.objects.bulk_create(objects)
		print("{0:8d} AlternateNames loaded".format(processed))

	def handle(self, *args, **kwargs):
		# self.dir = options.get('dir')

		self.clear_tables()
		self.load_countries()
		self.load_admin1_codes()
		self.load_admin2_codes()

		# code for reloading country / admin1 / admin2 structs from the db if skipping load_countries / load_admin(1|2)_codes:
		#for country in Country.objects.all():
		#	self.countries[country.code] = {}
		#for admin1 in Admin1Code.objects.all():
		#	self.countries[admin1.country_id][admin1.code] = {'geonameid': admin1.geonameid, 'admins2': {}}
		#for admin2 in Admin2Code.objects.filter(admin1__isnull=False).select_related('admin1'):
		#	admin1_dic = self.countries[admin2.country_id].get(admin2.admin1.code)
		#	if admin1_dic:
		#		admin1_dic['admins2'][admin2.code] = admin2.geonameid
		self.load_localities()
		self.load_altnames()
