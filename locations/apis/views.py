from rest_framework.views import APIView
from locations.models import Country, State, City
from .serializers import CountrySerializer
from rest_framework.response import Response
from rest_framework import status
from django.db.utils import IntegrityError
from utilities import utils as ut
from django.db import transaction


class CountryCreateView(APIView):

    def post(self, request):
        countries_data = request.data.get("countries", [])

        if not isinstance(countries_data, list):
            payload = ut.get_payload(
                request, message="countries name should be in list form."
            )
            return Response(payload, status=status.HTTP_409_CONFLICT)

        country_names = [
            {"name": country["name"].upper(), "code": country["code"].upper()}
            for country in countries_data
        ]

        try:
            countries_to_create = [Country(**country) for country in country_names]
            Country.objects.bulk_create(countries_to_create)
        except IntegrityError as ie:
            payload = ut.get_payload(request, message=str(ie))
            return Response(payload, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            payload = ut.get_payload(request, message="Un-expected error occurse.")
            return Response(payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payload = ut.get_payload(request, message="Countries Created")
        return Response(payload, status=status.HTTP_201_CREATED)


class StateCreateView(APIView):

    def post(self, request):
        data = request.data

        if not isinstance(data, list):
            payload = ut.get_payload(
                request, message="Body data should be in list form."
            )
            return Response(payload, status=status.HTTP_409_CONFLICT)

        with transaction.atomic():
            states_data = []
            for _ in data:
                country_obj = Country.objects.filter(name__icontains=_.get("country"))
                if country_obj.exists():
                    for state in _.get("states"):
                        state_obj = State.objects.filter(
                            name__icontains=state, country=country_obj[0]
                        )
                        if not state_obj.exists():
                            states_ins = State(
                                name=state.upper(), country=country_obj[0]
                            )
                            states_data.append(states_ins)
            if states_data:
                State.objects.bulk_create(states_data)

        payload = ut.get_payload(request, message="States Created")
        return Response(payload, status=status.HTTP_201_CREATED)


class CityCreateView(APIView):

    def post(self, request):
        data = request.data

        if not isinstance(data, list):
            payload = ut.get_payload(
                request, message="Body data should be in list form."
            )
            return Response(payload, status=status.HTTP_409_CONFLICT)

        with transaction.atomic():
            cities_data = []
            for _ in data:
                country = _.get("country").upper()
                state = _.get("state").upper()
                cities = _.get("cities")

                country_qs = Country.objects.filter(name__icontains=country)
                if country_qs.exists():
                    state_qs = State.objects.filter(
                        name__icontains=state, country=country_qs[0]
                    )
                    if state_qs.exists():

                        for city in set(cities):
                            city_qs = City.objects.filter(
                                name__icontains=city, state=state_qs[0]
                            )
                            if not city_qs:
                                city_ins = City(name=city.upper(), state=state_qs[0])
                                cities_data.append(city_ins)

            if cities_data:
                City.objects.bulk_create(cities_data)

        payload = ut.get_payload(request, message="Cities Created SUccessfully.")
        return Response(payload, status=status.HTTP_201_CREATED)
