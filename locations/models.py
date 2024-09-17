from django.db import models
from leads.models import StudentLeads

# Create your models here.


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Name of the country
    code = models.CharField(
        max_length=10, unique=True, null=True, blank=True
    )  # Optional code for the country

    def __str__(self):
        return self.name
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]


class State(models.Model):
    name = models.CharField(max_length=100)  # Name of the state
    country = models.ForeignKey(
        Country, related_name="states", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]


class City(models.Model):
    name = models.CharField(max_length=100)  # Name of the city
    state = models.ForeignKey(State, related_name="cities", on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]

class Address(models.Model):
    lead = models.OneToOneField(
        StudentLeads, related_name="address", on_delete=models.CASCADE
    )
    address_line1 = models.CharField(
        max_length=255, null=True, blank=True
    )  # First line of the address
    address_line2 = models.CharField(
        max_length=255, null=True, blank=True
    )  # Second line of the address (optional)
    city = models.ForeignKey(
        City, on_delete=models.SET_NULL, null=True, blank=True
    )  # City of the address
    state = models.ForeignKey(
        State, on_delete=models.SET_NULL, null=True, blank=True
    )  # State of the address
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True
    )  # Country of the address
    postal_code = models.CharField(
        max_length=20, null=True, blank=True
    )  # Postal code of the address


    # class Meta:
    #     indexes = [
    #         models.Index(fields=['lead']),
    #         models.Index(fields=['country']),
    #         models.Index(fields=['state']),
    #         models.Index(fields=['city']),
    #     ]