from django import forms
from .models import Letter, LetterImage, Message, Profile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import json
from django.conf import settings
import os
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.forms.widgets import ClearableFileInput
from django.contrib.auth.password_validation import password_validators_help_text_html

LETTER_MIN_CHARS = 300
LETTER_MAX_CHARS = 2000
CITIES_FILE_PATH = os.path.join(settings.BASE_DIR, 'static', 'js', 'cities.json')

with open(CITIES_FILE_PATH, encoding='utf-8') as f:
    VALID_CITIES = set(json.load(f))

class LetterForm(forms.ModelForm):
    class Meta:
        model = Letter
        fields = ['letter_type', 'text_content', 'pdf']

    def __init__(self, *args, **kwargs):
        super(LetterForm, self).__init__(*args, **kwargs)
        self.fields['text_content'].widget = forms.Textarea(attrs={'rows': 4})
        self.fields['letter_type'].required = False
        self.fields['pdf'].required = False

    def clean(self):
        cleaned_data = super().clean()
        letter_type = cleaned_data.get('letter_type') or getattr(self.instance, 'letter_type', None)
        text_content = (cleaned_data.get('text_content') or '').strip()
        pdf = cleaned_data.get('pdf')

        # --- Text validation ---
        LETTER_MIN_CHARS = 300
        LETTER_MAX_CHARS = 2000
        if letter_type == 'text':
            if not text_content:
                raise forms.ValidationError('❌ You selected Text, but did not write anything.')
            if len(text_content) < LETTER_MIN_CHARS:
                raise forms.ValidationError(f'❌ Letter text must be at least {LETTER_MIN_CHARS} characters long.')
            if len(text_content) > LETTER_MAX_CHARS:
                raise forms.ValidationError(f'❌ Letter text must be {LETTER_MAX_CHARS} characters or fewer.')

        # --- PDF validation ---
        if letter_type == 'pdf':
            if not pdf and not getattr(self.instance, 'pdf', None):
                raise forms.ValidationError('❌ You selected PDF, but did not upload a file.')
            if pdf and not str(pdf.name).lower().endswith('.pdf'):
                raise forms.ValidationError('❌ Please upload a valid PDF file.')

        # --- Image validation ---
        if letter_type == 'image':
            images = self.files.getlist('images') if hasattr(self, 'files') else []
            if not images and not getattr(self.instance, 'images', None):
                raise forms.ValidationError('❌ Please upload at least one image.')
            for img in images:
                if not img.content_type.startswith('image/'):
                    raise forms.ValidationError('❌ Only image files are allowed for image letters.')

        return cleaned_data

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
        }
class CustomFileInput(ClearableFileInput):
        can_clear = False  # This disables the "Clear" checkbox
class ProfileForm(forms.ModelForm):
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Non-binary', 'Non-binary'),
        ('Other', 'Other'),
    ]

    PREFERRED_GENDER_CHOICES = [
        ('Any', 'Any'),
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Non-binary', 'Non-binary'),
        ('Other', 'Other'),
    ]

    CONNECTION_TYPE_CHOICES = [
        ('dating', 'Dating'),
        ('friendship', 'Friendship'),
        ('fun', 'Just here for the experience / letters'),
    ]
    preferred_age_min = forms.IntegerField(required=True, label="Preferred Min Age")
    preferred_age_max = forms.IntegerField(required=True, label="Preferred Max Age")

    gender = forms.ChoiceField(choices=GENDER_CHOICES)
    preferred_gender = forms.ChoiceField(choices=PREFERRED_GENDER_CHOICES, required=False)
    connection_types = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=CONNECTION_TYPE_CHOICES,
    )
    location = forms.CharField(required=False, label='City')

    only_same_city = forms.BooleanField(required=False, label="Only show matches from my city")  # ✅ added
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'profile_picture' in self.fields:
            self.fields['profile_picture'].widget = CustomFileInput()
    def clean(self):
        cleaned_data = super().clean()  # not leaned_data
        location = cleaned_data.get("location", "").strip()

        if not location:
            self.add_error("location", "City is required.")
        elif location not in VALID_CITIES:
            self.add_error("location", "Please enter a valid city name")

        return cleaned_data  # important to return it
    class Meta:
        model = Profile
        fields = [
            'age',
            'gender',
            'profile_picture',
            'preferred_gender',
            'preferred_age_min',
            'preferred_age_max',
            'connection_types',
            'location',
            'only_same_city'  # ✅ include in fields
        ]

    def clean_connection_types(self):
        data = self.cleaned_data.get('connection_types')
        if not data:
            raise forms.ValidationError("Please select at least one connection type.")
        return data
    

class LetterFilterForm(forms.Form):
    min_age = forms.IntegerField(required=False, label='Min Age')
    max_age = forms.IntegerField(required=False, label='Max Age')
    gender = forms.ChoiceField(
        required=False,
        choices=[('', 'Any'), ('Male', 'Male'), ('Female', 'Female')],
        label='Gender'
    )

class FullRegisterForm(UserCreationForm):
    CONNECTION_TYPE_CHOICES = [
        ('dating', 'Dating'),
        ('friendship', 'Friendship'),
        ('fun', 'Just here for the experience / letters'),
    ]

    name = forms.CharField(required=True, label="Name")
    email = forms.EmailField(required=True)
    age = forms.IntegerField(required=True)
    gender = forms.ChoiceField(
        choices=[
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Non-binary', 'Non-binary'),
            ('Other', 'Other'),
        ]
    )
    # keep required=True by default
    profile_picture = forms.ImageField(required=True, label="Profile picture")

    preferred_gender = forms.ChoiceField(
        choices=[
            ('Any', 'Any'),
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Non-binary', 'Non-binary'),
            ('Other', 'Other'),
        ],
        required=False
    )

    preferred_age_min = forms.IntegerField(required=True, label="Preferred Minimum Age")
    preferred_age_max = forms.IntegerField(required=True, label="Preferred Maximum Age")

    connection_types = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=CONNECTION_TYPE_CHOICES,
    )

    location = forms.CharField(required=False, label='City')
    event_code = forms.CharField(
        required=False,
        label="Event code (if you joined an in-person event)",
        help_text="Leave empty if you're not using a physical event code."
    )
    letter_type = forms.ChoiceField(
        required=False,
        choices=[('text', 'Text'), ('image', 'Image'), ('pdf', 'PDF')],
        label="Letter Type (optional)"
    )
    text_content = forms.CharField(widget=forms.Textarea, required=False, label="Letter Text")
    pdf = forms.FileField(required=False)
    only_same_city = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=[("yes", " Only show matches from my city")]
    )

    class Meta:
        model = User
        fields = [
            'name', 'email', 'password1', 'password2',
            'age', 'gender', 'profile_picture',
            'preferred_gender', 'preferred_age_min', 'preferred_age_max',
            'connection_types', 'location',
            'letter_type', 'text_content', 'pdf',
            'agree_to_share',
        ]

    # NEW: conditionally relax the HTML/browser "required" only when a temp picture exists
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].help_text = password_validators_help_text_html()
        self.fields["password2"].help_text = "Enter the same password as before, for verification."

        temp_path = (self.data.get("temp_profile_picture") or "").strip() if hasattr(self, "data") else ""
        if temp_path:
            # don’t force the browser to re-upload; server will validate presence via temp
            self.fields["profile_picture"].required = False
            self.fields["profile_picture"].widget.attrs.pop("required", None)

    def clean_connection_types(self):
        data = self.cleaned_data.get('connection_types')
        if not data:
            raise forms.ValidationError("Please select at least one connection type.")
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

    def clean(self):
        cleaned_data = super().clean()
        location = cleaned_data.get("location", "").strip()

        if not location:
            self.add_error("location", "City is required.")
        elif location not in VALID_CITIES:
            self.add_error("location", "Please enter a valid city name")

        # ✅ still required overall: must have either a fresh upload OR a stashed temp file
        profile_picture = cleaned_data.get("profile_picture")
        temp_path = (self.data.get("temp_profile_picture") or "").strip()
        if not profile_picture and not temp_path:
            self.add_error("profile_picture", "Please upload a profile picture.")

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("🚫 This email address is already in use. Try logging in instead.")
        return email

    agree_to_share = forms.BooleanField(
        required=True,
        label="We will share your information with your potential matches. Do you agree with that?"
    )

class LetterImageForm(forms.ModelForm):
    class Meta:
        model = LetterImage
        fields = ['image']
