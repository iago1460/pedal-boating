import datetime

from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.utils import DatabaseError, OperationalError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import FormView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView

from boating.forms import BookingForm, HomeForm
from boating.models import Booking, HirePoint, SLOT_TIME
from boating.utils import generate_url


def place_booking(hire_point, name, start_time, duration, number_of_people):
    """
    This code runs in an atomic transaction to avoid concurrency issues during the booking process
    :param hire_point:
    :param name:
    :param start_time:
    :param duration:
    :param number_of_people:
    :return: booking object
    :raises: DatabaseError if something is not correct
    """
    end_time = start_time + duration
    with transaction.atomic():
        if not hire_point.is_open(time=start_time) or not hire_point.is_open(time=end_time):
            raise OperationalError('The hire_point is close')
        boats = hire_point.is_available(start_time=start_time, people=number_of_people, duration=duration)
        if not boats:
            raise OperationalError('No boats available')
        booking = Booking.objects.create(
            name=name, hire_point=hire_point, number_of_people=number_of_people,
            start_time=start_time, end_time=end_time
        )
        booking.boats.add(*boats)
        return booking


def get_slots(hire_point, date, number_of_people, duration):
    """
    Generate a list of all the possible schedules available in a hire_point
    :param hire_point:
    :param date:
    :param number_of_people:
    :param duration:
    :return: A list of tuples, the first element represents the slot id,
    the second element is its verbose name, the third element tell us if the slot is available
    and the last element a selection of boats that the user will use
    """
    available_slots, available_boats = hire_point.get_available_slots(
        date=date,
        people=number_of_people,
        duration=duration
    )
    available_slots = [_date.strftime('%Y-%m-%d %H:%M:%S') for _date in available_slots]
    slots = []
    start_time = hire_point.get_start_time(date)
    closing_time = hire_point.get_closing_time(date)
    if start_time and closing_time:
        from_hour = start_time
        while from_hour + duration <= closing_time:
            to_hour = from_hour + duration
            slot_id = from_hour.strftime('%Y-%m-%d %H:%M:%S')
            verbose_name = '%s - %s' % (
                from_hour.strftime('%I:%M %p'), to_hour.strftime('%I:%M %p')
            )
            try:
                index = available_slots.index(slot_id)
            except ValueError:
                is_available = False
                boats = []
            else:
                is_available = True
                boats = available_boats[index]

            slots.append((slot_id, verbose_name, is_available, boats))
            from_hour += datetime.timedelta(minutes=SLOT_TIME)
    return slots


class HomeView(FormView):
    form_class = HomeForm
    template_name = 'hire_point/home.html'

    def get_success_url(self, hire_point):
        return reverse('booking', args=[hire_point.pk])

    def form_valid(self, form):
        date = form.cleaned_data['date']
        duration = form.cleaned_data['duration']
        name = form.cleaned_data['name']
        number_of_people = form.cleaned_data['number_of_people']
        hire_point = form.cleaned_data['hire_point']

        parameters = {
            'date': date,
            'duration': duration,
            'name': name,
            'number_of_people': number_of_people,
        }
        url = generate_url(self.get_success_url(hire_point), parameters)
        return HttpResponseRedirect(url)


class BookingView(FormView):
    form_class = BookingForm
    template_name = 'hire_point/available_slots.html'

    hire_point = None
    date = None
    duration = None
    number_of_people = None
    name = None

    def dispatch(self, request, *args, **kwargs):
        self.hire_point = get_object_or_404(HirePoint, pk=kwargs['pk'])
        return super(BookingView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self, booking):
        return reverse('booking_successful', args=[booking.id])

    def get_unsuccess_url(self):
        return reverse('booking_unsuccessful')

    def get_initial(self):
        initial = super(BookingView, self).get_initial()
        initial.update({
            'name': self.name,
            'duration': self.duration,
            'number_of_people': self.number_of_people,
            'hire_point': self.hire_point,
        })
        return initial

    def get_context_data(self, **kwargs):
        context = super(BookingView, self).get_context_data(**kwargs)
        duration = datetime.timedelta(minutes=int(self.duration))

        slots = get_slots(
            hire_point=self.hire_point, date=self.date, number_of_people=self.number_of_people, duration=duration
        )

        url = reverse('booking', args=[self.hire_point.pk])
        parameters = {
            'duration': self.duration,
            'name': self.name,
            'number_of_people': self.number_of_people,
            'date': self.date + datetime.timedelta(days=1)
        }
        next_url = generate_url(url, parameters)
        parameters['date'] = self.date + datetime.timedelta(days=-1)
        previous_url = generate_url(url, parameters)

        context.update({
            'today': self.date,
            'next_url': next_url,
            'previous_url': previous_url,
            'slots': slots,
            'boats': self.hire_point.boats.all(),
            'bookings': Booking.get_bookings_between(
                hire_point=self.hire_point,
                start_time=datetime.datetime.combine(self.date, datetime.time.min),
                end_time=datetime.datetime.combine(self.date, datetime.time.max) + datetime.timedelta(days=1)
            ).order_by('start_time'),
        })
        return context

    def get(self, request, *args, **kwargs):
        self.date = datetime.datetime.strptime(request.GET.get('date'), '%Y-%m-%d').date()
        self.duration = request.GET.get('duration')
        self.name = request.GET.get('name')
        self.number_of_people = int(request.GET.get('number_of_people'))
        return super(BookingView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        start_time = form.cleaned_data['start_time']
        duration = form.cleaned_data['duration']
        hire_point = form.cleaned_data['hire_point']
        name = form.cleaned_data['name']
        number_of_people = form.cleaned_data['number_of_people']

        try:
            booking = place_booking(hire_point, name, start_time, duration, number_of_people)
            return HttpResponseRedirect(self.get_success_url(booking))
        except DatabaseError:
            return HttpResponseRedirect(self.get_unsuccess_url())

    def form_invalid(self, form):
        return HttpResponseRedirect(self.get_unsuccess_url())


class BookingSuccessfulView(DetailView):
    model = Booking
    template_name = 'hire_point/booking_successful.html'


class BookingUnsuccessfulView(TemplateView):
    template_name = 'hire_point/booking_unsuccessful.html'
