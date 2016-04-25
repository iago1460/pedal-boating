from django.contrib import admin

from boating.models import HirePoint, OpeningTimes, Boat, Booking


class OpeningTimesInline(admin.TabularInline):
    model = OpeningTimes
    extra = 0


class HirePointBoatInline(admin.TabularInline):
    model = Boat
    extra = 0


class HirePointAdmin(admin.ModelAdmin):
    model = HirePoint
    inlines = [HirePointBoatInline, OpeningTimesInline]


admin.site.register(HirePoint, HirePointAdmin)


class BookingAdmin(admin.ModelAdmin):
    model = Booking
    list_filter = ('hire_point',)


admin.site.register(Booking, BookingAdmin)
