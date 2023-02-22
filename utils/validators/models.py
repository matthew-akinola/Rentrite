from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_NIN_digits(value):
    if not value.isnumeric():
        raise ValidationError(
            _("%(value)s is not a valid NIN"),
            params={"value": value},
        )

def validate_file_size(file):
    max_size = 5000
    if file.size > max_size * 1024:
        raise ValidationError(f"file cannot be larger than {str(max_size)[0]}MB")
    
    return file