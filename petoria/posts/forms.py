from django import forms
from .models import BasePost, Lost_found_post, Surrender_custody_pets
import phonenumbers

class Lost_found_post(forms.ModelForm):
    class Meta:
        model = Lost_found_post
        fields = ['title', 'description', 'user', 'PostImage', 'contact_phone', 'contact_email', 'pet_name', 'location']

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        if phone:
            try:
                number = phonenumbers.parse(str(phone))
                if not phonenumbers.is_valid_number(number):
                    raise forms.ValidationError("Invalid phone number")
            except phonenumbers.NumberParseException:
                raise forms.ValidationError("Invalid phone number format")
        return phone