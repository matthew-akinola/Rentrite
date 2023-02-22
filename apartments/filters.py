from django_filters.filterset import FilterSet

from .models import Apartment


class ApartmentFilter(FilterSet):
    class Meta:
        model = Apartment
        fields = {
            "category": ["exact"],
            "_type": ["exact"],
            "address": ["icontains"],
            "price": ["gt", "lt"],
            "agent__first_name": ["icontains"],
            "agent__last_name": ["icontains"],
        }
 