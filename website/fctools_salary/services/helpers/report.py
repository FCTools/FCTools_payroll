"""
Copyright © 2020-2021 FC Tools.
All rights reserved.
Author: German Yakimov
"""

from django.db import transaction

from fctools_salary.models import Report as Rp
from fctools_salary.services.helpers.pdf_generator import PDFGenerator


class Report:
    def __init__(self):
        self.start_balances = {}
        self.traffic_groups = {}
        self.profits = {}
        self.revenues = {}
        self.deltas = {}
        self.tests = {}
        self.from_other_users = {}
        self.final_percents = {}
        self.result = {}
        self.user = None
        self.start_date = None
        self.end_date = None

        self._report_generator = PDFGenerator()

    def generate_pdf(self):
        return self._report_generator.generate_report_upd(self.revenues, self.final_percents, self.start_balances,
                                                          self.profits, self.deltas, self.tests,
                                                          self.from_other_users, self.result, self.user,
                                                          self.start_date, self.end_date)

    def _save_user_balances(self):
        """
        Saves user balances to database.
        """

        with transaction.atomic():
            self.user.admin_balance = self.result["ADMIN"][1] if "ADMIN" in self.result and self.result["ADMIN"][
                1] < 0 else 0
            self.user.fpa_hsa_pwa_balance = (
                self.result["FPA/HSA/PWA"][1] if "FPA/HSA/PWA" in self.result and self.result["FPA/HSA/PWA"][
                    1] < 0 else 0
            )
            self.user.inapp_balance = self.result["INAPP traff"][1] if "INAPP traff" in self.result and self.result[
                "INAPP traff"][1] < 0 else 0
            self.user.native_balance = (
                self.result["NATIVE traff"][1] if "NATIVE traff" in self.result and self.result["NATIVE traff"][
                    1] < 0 else 0
            )
            self.user.pop_balance = self.result["POP traff"][1] if "POP traff" in self.result and \
                                                                   self.result["POP traff"][1] < 0 else 0
            self.user.push_balance = self.result["PUSH traff"][1] if "PUSH traff" in self.result and \
                                                                     self.result["PUSH traff"][1] < 0 else 0
            self.user.tik_tok_balance = self.result["Tik Tok"][1] if "Tik Tok" in self.result and \
                                                                     self.result["Tik Tok"][1] < 0 else 0

            self.user.save()

    def _save_profits(self, report):
        report.profit_admin = self.profits["ADMIN"] if "ADMIN" in self.profits else None
        report.profit_fpa_hsa_pwa = self.profits["FPA/HSA/PWA"] if "FPA/HSA/PWA" in self.profits else None
        report.profit_inapp = self.profits["INAPP traff"] if "INAPP traff" in self.profits else None
        report.profit_native = self.profits["NATIVE traff"] if "NATIVE traff" in self.profits else None
        report.profit_pop = self.profits["POP traff"] if "POP traff" in self.profits else None
        report.profit_push = self.profits["PUSH traff"] if "PUSH traff" in self.profits else None
        report.profit_tik_tok = self.profits["Tik Tok"] if "Tik Tok" in self.profits else None

        return report

    def _save_percents(self, report):
        report.percent_admin = self.final_percents["ADMIN"] if "ADMIN" in self.final_percents else None
        report.percent_fpa_hsa_pwa = self.final_percents[
            "FPA/HSA/PWA"] if "FPA/HSA/PWA" in self.final_percents else None
        report.percent_inapp = self.final_percents["INAPP traff"] if "INAPP traff" in self.final_percents else None
        report.percent_native = self.final_percents["NATIVE traff"] if "NATIVE traff" in self.final_percents else None
        report.percent_pop = self.final_percents["POP traff"] if "POP traff" in self.final_percents else None
        report.percent_push = self.final_percents["PUSH traff"] if "PUSH traff" in self.final_percents else None
        report.percent_tik_tok = self.final_percents["Tik Tok"] if "Tik Tok" in self.final_percents else None

        return report

    def save(self):
        self._save_user_balances()

        report = Rp(user=self.user, start_date=self.start_date, end_date=self.end_date)
        report = self._save_profits(report)
        report = self._save_percents(report)

        report.save()

    def generate_deltas_calculation(self):
        result = {}

        for traffic_group in self.traffic_groups:
            result[traffic_group] = ["", 0.0]

            if not self.deltas[traffic_group]:
                result[traffic_group][0] = "0.0"
                continue

            for period in self.deltas[traffic_group]:
                deltas_value = self.deltas[traffic_group][period][0]
                percent = self.deltas[traffic_group][period][1]

                if result[traffic_group][0]:
                    result[traffic_group][0] += f" + {deltas_value}*{percent} [{period}]"
                else:
                    result[traffic_group][0] += f"{deltas_value}*{percent} [{period}]"

                result[traffic_group][1] += deltas_value * percent

            result[traffic_group][1] = round(result[traffic_group][1], 6)

            if "+" in result[traffic_group][0]:
                result[traffic_group][0] += f" = {result[traffic_group][1]}"

        return result

    def generate_calculation(self):
        self.deltas = self.generate_deltas_calculation()

        for traffic_group in self.traffic_groups:
            self.result[traffic_group] = ["", 0.0]

            # start balances
            self.result[traffic_group][1] += self.start_balances[traffic_group]

            # profits
            self.result[traffic_group][1] += self.profits[traffic_group]

            # tests
            self.result[traffic_group][1] += self.tests[traffic_group][1]

            # percent multiplying
            if self.start_balances[traffic_group] + self.profits[traffic_group] + self.tests[traffic_group][1] > 0:
                self.result[traffic_group][1] *= self.final_percents[traffic_group]

                self.result[traffic_group][0] = "({} + {} + {}) * {}".format(
                    self.start_balances[traffic_group],
                    self.profits[traffic_group],
                    self.tests[traffic_group][1],
                    self.final_percents[traffic_group]
                )
            else:
                self.result[traffic_group][0] = "{} + {} + {}".format(
                    self.start_balances[traffic_group],
                    self.profits[traffic_group],
                    self.tests[traffic_group][1],
                )

            # from other users
            self.result[traffic_group][1] += self.from_other_users[traffic_group][1]

            # deltas
            self.result[traffic_group][1] += self.deltas[traffic_group][1]

            self.result[traffic_group][0] = "{} + {} + {} = {}".format(
                self.result[traffic_group][0],
                self.from_other_users[traffic_group][1],
                self.deltas[traffic_group][1],
                self.result[traffic_group][1]
            )
