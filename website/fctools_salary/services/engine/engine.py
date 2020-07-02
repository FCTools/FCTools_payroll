from copy import deepcopy
from datetime import timedelta

from fctools_salary.models import Campaign, Test
from fctools_salary.services.binom.get_info import get_campaigns


def count_final_percent(revenue, salary_group):
    if salary_group == 1:
        percent = 0.5

        if revenue > 10000:
            percent = 0.6
        elif revenue > 5000:
            percent = 0.55
    else:
        percent = 0.3

        if revenue > 20000:
            percent = 0.4
        elif revenue > 10000:
            percent = 0.35

    return percent


def count_user_salary(user, start_date, end_date, update_db):
    report = ''

    result = {'ADMIN': round(float(user.admin_balance), 6),
              'FPA/HSA/PWA': round(float(user.fpa_hsa_pwa_balance), 6),
              'INAPP traff': round(float(user.inapp_balance), 6),
              'NATIVE traff': round(float(user.native_balance), 6),
              'POP traff': round(float(user.pop_balance), 6),
              'PUSH traff': round(float(user.push_balance), 6)}

    start_balances = deepcopy(result)

    report += f'<b>Start balances:</b>\n<br>\nADMIN: {result["ADMIN"]}\n<br>\nFPA/HSA/PWA: ' \
              f'{result["FPA/HSA/PWA"]}\n<br>\n' \
              f'INAPP traff: {result["INAPP traff"]}\n<br>\nNATIVE traff: {result["NATIVE traff"]}\n<br>\n' \
              f'POP traff: {result["POP traff"]}\n<br>\nPUSH traff: {result["PUSH traff"]}\n<br>\n\n<br>\n'

    prev_campaigns_db_list = list(Campaign.objects.filter(user=user))

    prev_campaigns_tracker = get_campaigns(start_date - timedelta(days=14), start_date - timedelta(days=1), user)
    current_campaigns_tracker = get_campaigns(start_date, end_date, user)

    total_revenue = 0.0

    for campaign in current_campaigns_tracker:
        total_revenue += float(campaign['campaign'].revenue)

        if campaign['campaign'].traffic_group in result:
            result[campaign['campaign'].traffic_group] += float(campaign['campaign'].profit)

    report += '<b>Profits: </b>\n<br>\n'

    profits = {}

    for traffic_group in result:
        report += f'{traffic_group}: {round(result[traffic_group] - start_balances[traffic_group], 6)}\n<br>\n'
        profits[traffic_group] = round(result[traffic_group] - start_balances[traffic_group], 6)

    report += '\n<br>\n'

    from_prev_period = {'ADMIN': ['', 0.0],
                        'FPA/HSA/PWA': ['', 0.0],
                        'INAPP traff': ['', 0.0],
                        'NATIVE traff': ['', 0.0],
                        'POP traff': ['', 0.0],
                        'PUSH traff': ['', 0.0]}

    for campaign_obj in prev_campaigns_tracker:
        campaign = campaign_obj['campaign']

        if campaign in prev_campaigns_db_list:
            campaign_db_profit = [x for x in prev_campaigns_db_list if x.id == campaign.id][0].profit

            if campaign.profit > campaign_db_profit:
                diff = float(campaign.profit - campaign_db_profit)

                if campaign.traffic_group in result:
                    result[campaign.traffic_group] += diff

                    if from_prev_period[campaign.traffic_group][1] > 0:
                        from_prev_period[campaign.traffic_group][0] += f" + {diff}"
                        from_prev_period[campaign.traffic_group][1] += diff
                    else:
                        from_prev_period[campaign.traffic_group][0] = f"{diff}"
                        from_prev_period[campaign.traffic_group][1] += diff

    report += '<b>From previous period:</b>\n<br>\n'

    for traffic_group in from_prev_period:
        from_prev_period[traffic_group][1] = round(from_prev_period[traffic_group][1], 6)

        if from_prev_period[traffic_group][1] == 0.0:
            report += f'{traffic_group}: 0.0\n<br>\n'
            from_prev_period[traffic_group][0] = '0.0'

        elif '+' in from_prev_period[traffic_group][0]:
            report += f'{traffic_group}: {from_prev_period[traffic_group][0]} = {from_prev_period[traffic_group][1]}' \
                      f'\n<br>\n'

            from_prev_period[traffic_group][0] = f'{from_prev_period[traffic_group][0]} = ' \
                                                 f'{from_prev_period[traffic_group][1]}'

    report += '\n<br>\n'

    tests_list = list(Test.objects.filter(user=user))
    done_current_campaigns = []

    tests = {'ADMIN': ['', 0.0],
             'FPA/HSA/PWA': ['', 0.0],
             'INAPP traff': ['', 0.0],
             'NATIVE traff': ['', 0.0],
             'POP traff': ['', 0.0],
             'PUSH traff': ['', 0.0]}

    # optimize that
    for test in tests_list:
        current_campaigns_list = []
        test_offers_ids = {offer.id for offer in list(test.offers.all())}
        test_traffic_sources_ids = [ts.id for ts in list(test.traffic_sources.all())]
        start_balance = test.balance
        test_balance = test.balance

        for campaign in current_campaigns_tracker:
            if campaign['campaign'].ts_id.id in test_traffic_sources_ids and \
                    len(test_offers_ids & set(campaign['offers_list'])) != 0:
                current_campaigns_list.append(campaign['campaign'])

        for campaign in current_campaigns_list:
            if campaign in done_current_campaigns:
                continue

            if campaign.profit >= 0:
                test_balance += campaign.profit
                done_current_campaigns.append(campaign)
                continue

            if test_balance >= 0 and test_balance + campaign.profit < 0 and campaign.traffic_group in result:
                result[campaign.traffic_group] += round(float(test_balance), 6)

                if tests[campaign.traffic_group][1] > 0:
                    tests[campaign.traffic_group][0] += f' + {round(float(test_balance), 6)}'
                else:
                    tests[campaign.traffic_group][0] += f'{round(float(test_balance), 6)}'

                tests[campaign.traffic_group][1] += round(float(test_balance), 6)

            elif test_balance >= 0 and test_balance + campaign.profit >= 0 and campaign.traffic_group in result:
                result[campaign.traffic_group] -= round(float(campaign.profit), 6)

                if tests[campaign.traffic_group][1] > 0:
                    tests[campaign.traffic_group][0] += f' + {-round(float(campaign.profit), 6)}'
                else:
                    tests[campaign.traffic_group][0] += f'{-round(float(campaign.profit), 6)}'

                tests[campaign.traffic_group][1] -= round(float(campaign.profit), 6)

            test_balance += campaign.profit
            done_current_campaigns.append(campaign)

        if update_db and test_balance != start_balance:
            test.balance = test_balance
            test.save()

    report += '<b>Tests:</b>\n<br>\n'

    for traffic_group in tests:
        tests[traffic_group][1] = round(tests[traffic_group][1], 6)
        if tests[traffic_group][1] == 0.0:
            report += f'{traffic_group}: 0.0\n<br>\n'
            tests[traffic_group][0] = '0.0'
        elif '+' in tests[traffic_group][0]:
            report += f'{traffic_group}: {tests[traffic_group][0]} = {tests[traffic_group][1]}' \
                      f'\n<br>\n'
            tests[traffic_group][0] = f'{tests[traffic_group][0]} = {tests[traffic_group][1]}'

    report += '\n<br>\n'

    if user.is_lead:
        # add percent here
        pass

    percent = count_final_percent(total_revenue, user.group)

    report += f'<b>Total revenue:</b> {total_revenue}\n<br>\n'
    report += f'<b>Final percent:</b> {percent}\n<br>\n\n<br>\n'
    report += f'<b>Summary: </b>\n<br>\n'

    for traffic_group in result:
        if result[traffic_group] > 0:
            result[traffic_group] *= percent
            result[traffic_group] = round(result[traffic_group], 6)

        result[traffic_group] = ['', result[traffic_group]]

        if result[traffic_group][1] >= 0:
            result[traffic_group][
                0] = f'({start_balances[traffic_group]}' \
                     f'{f" + {profits[traffic_group]}" if profits[traffic_group] >= 0 else f" - {-profits[traffic_group]}"}' \
                     f' + {from_prev_period[traffic_group][1]} + ' \
                     f'{tests[traffic_group][1]}) * {percent} = {result[traffic_group][1]}'
        else:
            result[traffic_group][
                0] = f'{start_balances[traffic_group]}' \
                     f'{f" + {profits[traffic_group]}" if profits[traffic_group] >= 0 else f" - {-profits[traffic_group]}"}' \
                     f' + {from_prev_period[traffic_group][1]} + ' \
                     f'{tests[traffic_group][1]} = {result[traffic_group][1]}'

    if update_db:
        user.admin_balance = result['ADMIN'] if result['ADMIN'] < 0 else 0
        user.fpa_hsa_pwa_balance = result['FPA/HSA/PWA'] if result['FPA/HSA/PWA'] < 0 else 0
        user.inapp_balance = result['INAPP traff'] if result['INAPP traff'] < 0 else 0
        user.native_balance = result['NATIVE traff'] if result['NATIVE traff'] < 0 else 0
        user.pop_balance = result['POP traff'] if result['POP traff'] < 0 else 0
        user.push_balance = result['PUSH traff'] if result['PUSH traff'] < 0 else 0

        user.save()

        for campaign in current_campaigns_tracker:
            campaign['campaign'].save()

    # return result, report
    return round(total_revenue, 6), percent, start_balances, profits, from_prev_period, tests, result
