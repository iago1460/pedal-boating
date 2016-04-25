import datetime

from django.test import TestCase

from boating.choices import MONDAY, SATURDAY, SUNDAY
from boating.models import Booking, OpeningTimes, HirePoint, Boat
from boating.views import place_booking


class HirePointMixin(object):
    hire_point1 = None
    hire_point2 = None

    def setUp(self):
        hire_point1 = HirePoint.objects.create(name='HirePoint 1', description='Mon-Fri')
        hire_point2 = HirePoint.objects.create(name='HirePoint 2', description='Weekend')

        for day in range(MONDAY, SATURDAY):
            OpeningTimes.objects.create(
                hire_point=hire_point1, day=day, from_hour=datetime.time(hour=9), to_hour=datetime.time(hour=20)
            )

        for day in [SATURDAY, SUNDAY]:
            OpeningTimes.objects.create(
                hire_point=hire_point2, day=day, from_hour=datetime.time(hour=7), to_hour=datetime.time(hour=23)
            )

        self.hire_point1 = hire_point1
        self.hire_point2 = hire_point2


class HirePointTestCase(HirePointMixin, TestCase):
    def test_opening_hours(self):
        # datetime.date(2016, 2, day) Monday is day one on February
        for day in range(MONDAY, SATURDAY):
            # hire_point 1
            self.assertEqual(
                self.hire_point1.get_start_time(datetime.date(2016, 2, day)),
                datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(9, 0, 0))
            )
            self.assertEqual(
                self.hire_point1.get_closing_time(datetime.date(2016, 2, day)),
                datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(20, 0, 0))
            )
            # estaurant 2
            self.assertIsNone(self.hire_point2.get_start_time(datetime.date(2016, 2, day)))
            self.assertIsNone(self.hire_point2.get_closing_time(datetime.date(2016, 2, day)))

        for day in [SATURDAY, SUNDAY]:
            # hire_point 1
            self.assertIsNone(self.hire_point1.get_start_time(datetime.date(2016, 2, day)))
            self.assertIsNone(self.hire_point1.get_closing_time(datetime.date(2016, 2, day)))
            # hire_point 2
            self.assertEqual(
                self.hire_point2.get_start_time(datetime.date(2016, 2, day)),
                datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(7, 0, 0))
            )
            self.assertEqual(
                self.hire_point2.get_closing_time(datetime.date(2016, 2, day)),
                datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(23, 0, 0))
            )

    def test_is_open(self):
        # datetime.date(2016, 2, day) Monday is day one on February
        for day in range(MONDAY, SATURDAY):
            # hire_point 1
            self.assertFalse(
                self.hire_point1.is_open(
                    datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(8, 59, 59))
                )
            )
            self.assertTrue(
                self.hire_point1.is_open(
                    datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(9, 0, 0))
                )
            )
            self.assertTrue(
                self.hire_point1.is_open(
                    datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(20, 0, 0))
                )
            )
            self.assertFalse(
                self.hire_point1.is_open(
                    datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(20, 0, 1))
                )
            )
            # hire_point 2
            self.assertFalse(
                self.hire_point2.is_open(
                    datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(12, 0, 0))
                )
            )

        for day in [SATURDAY, SUNDAY]:
            # hire_point 1
            self.assertFalse(
                self.hire_point1.is_open(
                    datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(12, 0, 0))
                )
            )
            # hire_point 2
            self.assertFalse(
                self.hire_point2.is_open(
                    datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(6, 59, 59))
                )
            )
            self.assertTrue(
                self.hire_point2.is_open(
                    datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(7, 0, 0))
                )
            )
            self.assertTrue(
                self.hire_point2.is_open(
                    datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(23, 0, 0))
                )
            )
            self.assertFalse(
                self.hire_point2.is_open(
                    datetime.datetime.combine(datetime.date(2016, 2, day), datetime.time(23, 0, 1))
                )
            )


class BookingTestCase(HirePointMixin, TestCase):
    boats_in_hire_point1 = None
    bookings_in_hire_point1 = None

    def setUp(self):
        super(BookingTestCase, self).setUp()

        boats_in_hire_point1 = []
        for seats in [2, 4, 4, 6]:
            boats_in_hire_point1.append(
                Boat.objects.create(hire_point=self.hire_point1, seats=seats)
            )
        self.boats_in_hire_point1 = boats_in_hire_point1

        bookings_in_hire_point1 = []
        booking1 = Booking.objects.create(
            name='Client1', number_of_people=1, hire_point=self.hire_point1,
            start_time=datetime.datetime(2016, 2, 1, 10, 0, 0), end_time=datetime.datetime(2016, 2, 1, 11, 0, 0)
        )
        booking1.boats.add(boats_in_hire_point1[0])
        bookings_in_hire_point1.append(booking1)

        booking2 = Booking.objects.create(
            name='Client2', number_of_people=1, hire_point=self.hire_point1,
            start_time=datetime.datetime(2016, 2, 2, 10, 0, 0), end_time=datetime.datetime(2016, 2, 2, 11, 0, 0)
        )
        booking2.boats.add(boats_in_hire_point1[0])
        bookings_in_hire_point1.append(booking2)
        self.bookings_in_hire_point1 = bookings_in_hire_point1

    def _check_boat(self, hire_point, people, start_time, end_time, assert_list):
        min_step = datetime.timedelta(minutes=15)
        time = start_time
        while time < end_time:
            boats_available = hire_point.is_available(people=people, start_time=time, duration=min_step * 2)
            time += min_step
            self.assertListEqual(boats_available, assert_list)

    def test_available_boats(self):
        hire_point = self.hire_point1
        for people in range(1, 3):
            start_time = datetime.datetime(2016, 2, 1, 9, 45, 0)
            end_time = datetime.datetime(2016, 2, 1, 9, 45, 0)
            assert_list = [self.boats_in_hire_point1[1]]
            self._check_boat(hire_point, people, start_time, end_time, assert_list)

            start_time = datetime.datetime(2016, 2, 1, 11, 0, 0)
            end_time = datetime.datetime(2016, 2, 1, 20, 0, 0)
            assert_list = [self.boats_in_hire_point1[0]]
            self._check_boat(hire_point, people, start_time, end_time, assert_list)

        people = 5
        start_time = datetime.datetime(2016, 2, 1, 9, 45, 0)
        end_time = datetime.datetime(2016, 2, 1, 9, 45, 0)
        assert_list = [self.boats_in_hire_point1[1], self.boats_in_hire_point1[2]]
        self._check_boat(hire_point, people, start_time, end_time, assert_list)

        start_time = datetime.datetime(2016, 2, 1, 11, 0, 0)
        end_time = datetime.datetime(2016, 2, 1, 20, 0, 0)
        assert_list = [self.boats_in_hire_point1[0], self.boats_in_hire_point1[1]]
        self._check_boat(hire_point, people, start_time, end_time, assert_list)

    def test_availability(self):
        hire_point = self.hire_point1
        date = datetime.date(2016, 2, 1)
        duration = datetime.timedelta(minutes=30)
        people = 5
        slots, boats = hire_point.get_available_slots(date, people, duration)
        self.assertEqual(len(slots), len(boats))
        for index, slot in enumerate(slots):
            if slot <= datetime.datetime(2016, 2, 1, 9, 30, 0):
                self.assertListEqual(boats[index], [self.boats_in_hire_point1[0], self.boats_in_hire_point1[1]])
            elif slot < datetime.datetime(2016, 2, 1, 11, 0, 0):
                self.assertListEqual(boats[index], [self.boats_in_hire_point1[1], self.boats_in_hire_point1[2]])
            else:
                self.assertListEqual(boats[index], [self.boats_in_hire_point1[0], self.boats_in_hire_point1[1]])

    def test_booking(self):
        hire_point = self.hire_point1
        start_time = datetime.datetime(2016, 2, 2, 9, 45, 0)
        duration = datetime.timedelta(minutes=30)
        people = 9
        name = 'Morning Party'

        booking = place_booking(hire_point, name, start_time, duration, people)
        self.assertSequenceEqual(booking.boats.all(), self.boats_in_hire_point1[1:4])

        start_time = datetime.datetime(2016, 2, 2, 10, 45, 0)
        booking = place_booking(hire_point, name, start_time, duration, people)
        self.assertSequenceEqual(booking.boats.all(), self.boats_in_hire_point1[1:4])

        date = start_time.date()
        people = 3
        slots, boats = hire_point.get_available_slots(date, people, duration)
        self.assertEqual(len(slots), len(boats))
        for index, slot in enumerate(slots):
            if slot < datetime.datetime(2016, 2, 2, 9, 30, 0):
                self.assertListEqual(boats[index], [self.boats_in_hire_point1[0], self.boats_in_hire_point1[1]])
            elif slot < datetime.datetime(2016, 2, 2, 10, 15, 0):
                raise RuntimeError('Cannot be any schedule available')
            elif slot == datetime.datetime(2016, 2, 2, 10, 15, 0):
                self.assertListEqual(boats[index], [self.boats_in_hire_point1[1]])
            elif slot < datetime.datetime(2016, 2, 2, 11, 15, 0):
                raise RuntimeError('Cannot be any schedule available')
            else:
                self.assertListEqual(boats[index], [self.boats_in_hire_point1[0], self.boats_in_hire_point1[1]])
