import json

from django.http import HttpResponse

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
