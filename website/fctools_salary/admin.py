# Register your models here.

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import User, Offer, TrafficSource, Test, Campaign, PercentDependency


# TODO: add table with salary groups (fields: id, rules). Maybe you need to create table for rules and use it
# TODO: with table for salary groups as m2m field

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
    def __init__(self, *args, **kwargs):
        super(TestForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(group__gt=0)
        self.fields['traffic_sources'].queryset = TrafficSource.objects.select_related('user').filter(user__group__gt=0)

    class Meta:
        model = Test
        fields = ('amount', 'user', 'offers', 'traffic_sources', 'traffic_group', 'balance',
                  'one_budget_for_all_traffic_sources')

    def clean_traffic_sources(self):
        traffic_sources_list = self.cleaned_data['traffic_sources']

        for traffic_source in traffic_sources_list.all():
            if traffic_source.user_id != self.cleaned_data['user'].id:
                raise ValidationError(f'Traffic source {traffic_source} pinned to another user.')

        return traffic_sources_list

    def clean_amount(self):
        amount = self.cleaned_data['amount']

        if amount <= 0:
            raise ValidationError('Test budget must be positive.')

        return amount

    def clean_balance(self):
        balance = self.cleaned_data['balance']

        if 'amount' in self.cleaned_data:
            amount = self.cleaned_data['amount']
        else:
            return balance

        if balance <= 0:
            raise ValidationError('Test balance must be positive')
        elif balance > amount:
            raise ValidationError("Test balance can't be greater than test budget.")
        else:
            return balance

    def clean(self):
        if 'traffic_sources' in self.cleaned_data:
            traffic_sources_list = self.cleaned_data['traffic_sources'].all()
        else:
            super(TestForm, self).clean()
            return

        if not self.instance.id:
            related_tests = Test.objects.filter(user=self.cleaned_data['user'],
                                                traffic_group=self.cleaned_data['traffic_group'])
            offers_list = ' ||| '.join(sorted([str(offer) for offer in self.cleaned_data['offers'].all()]))
            ts_list = ' ||| '.join(sorted([str(ts) for ts in traffic_sources_list]))

            for test in related_tests:
                if test.offers_list() == offers_list and test.traffic_sources_list() == ts_list:
                    raise ValidationError('This test already exists.')

        super(TestForm, self).clean()


def split_tests(modeladmin, request, queryset):
    for test in queryset:
        if not test.one_budget_for_all_traffic_sources:
            for traffic_source in test.traffic_sources.all():
                new_test = Test(user=test.user,
                                amount=test.amount,
                                balance=test.balance,
                                traffic_group=test.traffic_group)
                new_test.save()

                new_test.offers.add(*test.offers.all())
                new_test.traffic_sources.add(traffic_source)
                new_test.save()

            test.delete()
split_tests.short_description = 'Analyze by traffic sources'


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('offers_list', 'user', 'traffic_sources_list', 'traffic_group', 'amount_rounded', 'balance_colored')
    list_filter = ('user', 'traffic_group')
    list_select_related = ['user']
    form = TestForm
    save_as = True
    filter_horizontal = ('offers', 'traffic_sources',)
    actions = [split_tests]


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'traffic_group', 'ts_id', 'cost_rounded', 'revenue_rounded', 'profit_colored', 'user')
    list_display_links = ('id', 'name')
    list_filter = ('traffic_group', 'ts_id', 'user')
    list_select_related = ('ts_id', 'user')
    search_fields = ['name']


@admin.register(PercentDependency)
class PercentDependencyAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'percent')
    list_filter = ('from_user', 'to_user')
    list_select_related = ('from_user', 'to_user')
