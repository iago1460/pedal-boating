import datetime

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.six import python_2_unicode_compatible

from boating.choices import DAYS

SLOT_TIME = 15  # 15 minutes
MAX_DURATION = 60*3  # 3 hours


@python_2_unicode_compatible
class HirePoint(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def get_available_slots(self, date, people, duration):
        """
        Gets all the available schedules and the boats selected
        :param date:
        :param people:
        :param duration:
        :return: Two list with the same lenght, the first one contains the available slots
        and the second the boats to be used
        """
        slots = []
        boats = []
        time = self.get_start_time(date)
        closing_time = self.get_closing_time(date)
        while time < closing_time:
            boats_available = self.is_available(people=people, start_time=time, duration=duration)
            if boats_available:
                slots.append(time)
                boats.append(boats_available)
            time += datetime.timedelta(minutes=SLOT_TIME)
        return slots, boats

    def is_available(self, start_time, people, duration):
        """
        Check if there is any boat available in a concrete period
        :param start_time:
        :param people:
        :param duration:
        :return: A list of boats that the customer would use
        """
        collision_bookings = Booking.get_bookings_between(
            hire_point=self, start_time=start_time, end_time=start_time + duration
        )
        boats_per_booking = [_booking.boats.all() for _booking in collision_bookings]
        boats_in_use = set([_boat for _boats in boats_per_booking for _boat in _boats])

        selected_boats = []
        boats_allocations = 0
        free_boats = self.boats.all().exclude(id__in=[_boat.id for _boat in boats_in_use]).order_by('seats')
        for free_boat in free_boats:
            if free_boat.seats == people:  # perfect match
                return [free_boat]
            elif people > boats_allocations:  # if the space is still not enough
                boats_allocations += free_boat.seats
                selected_boats.append(free_boat)
            elif free_boat.seats > people:  # it's not necessary keep looking
                break

        if people <= boats_allocations:
            return selected_boats
        else:
            return None

    def get_start_time(self, date):
        try:
            opening_time = self.opening_times.get(day=date.isoweekday())
            return datetime.datetime.combine(date, opening_time.from_hour)
        except OpeningTimes.DoesNotExist:
            return None

    def get_closing_time(self, date):
        try:
            opening_time = self.opening_times.get(day=date.isoweekday())
            return datetime.datetime.combine(date, opening_time.to_hour)
        except OpeningTimes.DoesNotExist:
            return None

    def is_open(self, time):
        try:
            opening_time = self.opening_times.get(day=time.date().isoweekday())
            return opening_time.from_hour <= time.time() and opening_time.to_hour >= time.time()
        except OpeningTimes.DoesNotExist:
            pass
        return False


class OpeningTimes(models.Model):
    """
    Store opening times
    """
    hire_point = models.ForeignKey(HirePoint, related_name='opening_times')
    day = models.IntegerField(verbose_name='Day', choices=DAYS)
    from_hour = models.TimeField(verbose_name='Opening')
    to_hour = models.TimeField(verbose_name='Closing')


@python_2_unicode_compatible
class Boat(models.Model):
    """
    Store boats
    """
    hire_point = models.ForeignKey(HirePoint, related_name='boats')
    seats = models.IntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return 'Seats: %s' % self.seats


@python_2_unicode_compatible
class Booking(models.Model):
    """
    Store bookings
    """
    name = models.CharField(max_length=50)
    number_of_people = models.IntegerField(validators=[MinValueValidator(1)])
    hire_point = models.ForeignKey(HirePoint, db_index=True, related_name='bookings')
    boats = models.ManyToManyField(Boat, related_name='bookings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return '%s' % self.name

    @classmethod
    def get_bookings_between(cls, hire_point, start_time, end_time):
        return cls.objects.filter(
            hire_point=hire_point
        ).filter(
            Q(start_time__lt=end_time, end_time__gt=start_time) |
            Q(start_time=end_time, end_time=start_time)
        )
