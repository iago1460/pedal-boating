import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from boating.choices import MONDAY, SATURDAY, SUNDAY, FRIDAY
from boating.models import HirePoint, OpeningTimes, Boat


class Command(BaseCommand):
    def _get_or_create_hire_point(self, name, description):
        hire_point, created = HirePoint.objects.get_or_create(
            name=name,
            description=description
        )
        return hire_point, created

    def _create_opening_hours(self, start_hour, closing_hour, day, hire_point):
        OpeningTimes.objects.create(
            hire_point=hire_point, day=day, from_hour=start_hour, to_hour=closing_hour
        )

    def _create_boats(self, hire_point, seats):
        for seat_number in seats:
            Boat.objects.create(
                hire_point=hire_point, seats=seat_number
            )

    def handle(self, *args, **options):
        # Create administrator user
        user, created = User.objects.get_or_create(
            username='admin', defaults={
                'is_superuser': True,
                'is_staff': True,
            }
        )
        if created:
            user.set_password('1234')
            user.save()

        # Create hire_points
        hire_point, created = self._get_or_create_hire_point(
            name='West Hire Point',
            description='Rowing boats and pedalos available to hire.'
        )
        if created:
            for day in range(MONDAY, SATURDAY):
                self._create_opening_hours(
                    hire_point=hire_point,
                    start_hour=datetime.time(hour=10),
                    closing_hour=datetime.time(hour=18),
                    day=day,
                )
            self._create_boats(hire_point=hire_point, seats=[2, 2, 4, 4, 6, 8])

        hire_point, created = self._get_or_create_hire_point(
            name='Weekend Kids Lake',
            description='Rowing boats and pedalos available to hire for kids.'
        )
        if created:
            for day in [FRIDAY, SATURDAY, SUNDAY]:
                self._create_opening_hours(
                    hire_point=hire_point,
                    start_hour=datetime.time(hour=9),
                    closing_hour=datetime.time(hour=23),
                    day=day,
                )
            self._create_boats(hire_point=hire_point, seats=[2, 4, 4, 4, 8])

        hire_point, created = self._get_or_create_hire_point(
            name='East Hire Point',
            description='Rowing boats and pedalos available to hire.'
        )
        if created:
            for day in range(MONDAY, SUNDAY + 1):
                self._create_opening_hours(
                    hire_point=hire_point,
                    start_hour=datetime.time(hour=11),
                    closing_hour=datetime.time(hour=20),
                    day=day,
                )
            self._create_boats(hire_point=hire_point, seats=[2, 2, 2, 2, 4, 4, 4])
