import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class ComplexPasswordValidator:
    """
    Require at least 8 chars with 1 lowercase, 1 uppercase, 1 digit, 1 special.
    """
    def __init__(self, min_length=8):
        self.min_length = min_length
        self.special = re.compile(r"[!@#$%^&*()_\-+=\[\]{};:'\",.<>/?\\|`~]")

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(_("This password must contain at least %(min)d characters."),
                                  params={"min": self.min_length})
        if not re.search(r"[a-z]", password):
            raise ValidationError(_("This password must contain a lowercase letter."))
        if not re.search(r"[A-Z]", password):
            raise ValidationError(_("This password must contain an uppercase letter."))
        if not re.search(r"\d", password):
            raise ValidationError(_("This password must contain a digit."))
        if not self.special.search(password):
            raise ValidationError(_("This password must contain a special character."))

    def get_help_text(self):
        return _("Your password must be at least %(min)d characters and include "
                 "a lowercase letter, an uppercase letter, a number, and a special character.") \
               % {"min": self.min_length}
