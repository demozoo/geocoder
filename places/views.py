import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from places.models import Locality


def search(request):
	query = request.GET.get('q')
	if query:
		places = Locality.search(query)[:10]
	else:
		places = Locality.objects.none()

	results = [
		{'id': place.pk, 'name': place.long_name}
		for place in places
	]

	return HttpResponse(json.dumps(results), content_type='application/json')


def show(request, locality_id):
	place = get_object_or_404(Locality, pk=locality_id)
	result = {
		'id': place.pk,
		'name': place.name,
		'full_name': place.long_name,
		'country_name': place.country.name if place.country else None,
		'country_code': place.country.code if place.country else None,
		'latitude': float(place.latitude),
		'longitude': float(place.longitude),
	}

	return HttpResponse(json.dumps(result), content_type='application/json')
