import datetime

from django import forms
from django.core.validators import MinValueValidator

from boating.models import HirePoint, Booking, MAX_DURATION, SLOT_TIME
from boating.utils import humanize_time


class CommonFieldsForm(forms.Form):
    name = Booking._meta.get_field('name').formfield()
    duration = forms.ChoiceField(
        choices=[(_value, humanize_time(_value)) for _value in range(SLOT_TIME, MAX_DURATION + 1, SLOT_TIME)]
    )
    number_of_people = Booking._meta.get_field('number_of_people').formfield()

    def __init__(self, *args, **kwargs):
        super(CommonFieldsForm, self).__init__(*args, **kwargs)
        self.fields['hire_point'] = forms.ModelChoiceField(queryset=HirePoint.objects.all())
        self.fields['number_of_people'].validators = [MinValueValidator(1)]


class HomeForm(CommonFieldsForm):
    date = forms.DateField(
        initial=datetime.date.today, input_formats=['%d/%m/%Y'], widget=forms.widgets.DateInput(format='%d/%m/%Y')
    )


class BookingForm(CommonFieldsForm):
    start_time = forms.DateTimeField()

    def __init__(self, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        for field_key in self.fields.keys():
            self.fields[field_key].widget = forms.HiddenInput()

    def clean_duration(self):
        duration = self.cleaned_data['duration']
        return datetime.timedelta(minutes=int(duration))
