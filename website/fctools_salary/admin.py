# Register your models here.

from django.contrib import admin

from .models import User, Offer, TrafficSource, Test, Campaign, PercentDependency


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    pass


@admin.register(TrafficSource)
class TrafficSourceAdmin(admin.ModelAdmin):
    pass


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    pass


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    pass


@admin.register(PercentDependency)
class PercentDependencyAdmin(admin.ModelAdmin):
    pass
