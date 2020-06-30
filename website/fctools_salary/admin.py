# Register your models here.

from django.contrib import admin

from .models import User, Offer, TrafficSource, Test, Campaign, PercentDependency


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'login', 'is_lead', 'group')
    list_display_links = ('id', 'login')


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'geo', 'group', 'network_name')
    list_display_links = ('id', 'name')


@admin.register(TrafficSource)
class TrafficSourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user')
    list_display_links = ('id', 'name')


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('offers_list', 'user', 'traffic_sources_list', 'traffic_group', 'amount_rounded', 'balance_colored')

    def offers_list(self, test):
        return ' ||| '.join([str(offer) for offer in test.offers.all()])

    def traffic_sources_list(self, test):
        return ' ||| '.join([str(ts) for ts in test.traffic_sources.all()])


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'traffic_group', 'ts_id', 'cost_rounded', 'revenue_rounded', 'profit_colored', 'user')
    list_display_links = ('id', 'name')


@admin.register(PercentDependency)
class PercentDependencyAdmin(admin.ModelAdmin):
    pass
