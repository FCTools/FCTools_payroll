# Register your models here.

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import User, Offer, TrafficSource, Test, Campaign, PercentDependency


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'login', 'is_lead', 'group')
    list_display_links = ('id', 'login')
    list_filter = ('is_lead', 'group')
    search_fields = ['login']


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'geo', 'group', 'network_name')
    list_display_links = ('id', 'name')
    list_filter = ('geo', 'group', 'network_name')
    search_fields = ['name']


@admin.register(TrafficSource)
class TrafficSourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user')
    list_display_links = ('id', 'name')
    list_filter = ['user']
    list_select_related = ['user']
    search_fields = ['name']


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ('amount', 'user', 'offers', 'traffic_sources', 'traffic_group', 'balance')

    def clean(self):
        if not self.instance.id:
            related_tests = Test.objects.filter(user=self.cleaned_data['user'],
                                                traffic_group=self.cleaned_data['traffic_group'])
            offers_list = ' ||| '.join(sorted([str(offer) for offer in self.cleaned_data['offers'].all()]))
            traffic_sources_list = ' ||| '.join(sorted([str(ts) for ts in self.cleaned_data['traffic_sources'].all()]))

            for test in related_tests:
                if test.offers_list() == offers_list and test.traffic_sources_list() == traffic_sources_list:
                    raise ValidationError('This test already exists.')

        super().clean()


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('offers_list', 'user', 'traffic_sources_list', 'traffic_group', 'amount_rounded', 'balance_colored')
    list_filter = ('user', 'traffic_group')
    list_select_related = ['user']
    form = TestForm


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'traffic_group', 'ts_id', 'cost_rounded', 'revenue_rounded', 'profit_colored', 'user')
    list_display_links = ('id', 'name')
    list_filter = ('traffic_group', 'ts_id', 'user')
    list_select_related = ('ts_id', 'user')
    search_fields = ['name']


@admin.register(PercentDependency)
class PercentDependencyAdmin(admin.ModelAdmin):
    pass

