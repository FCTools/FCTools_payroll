from pprint import pprint

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

    def generate_deltas_calculation(self):
        result = {}

        for traffic_group in self.traffic_groups:
            result[traffic_group] = ["", 0.0]

            for period in self.deltas[traffic_group]:
                if result[traffic_group][0]:
                    result[traffic_group][0] += f" + {round(self.deltas[traffic_group][period], 6)} [{period}]"
                else:
                    result[traffic_group][0] += f"{round(self.deltas[traffic_group][period], 0)} [{period}]"
                result[traffic_group][1] += self.deltas[traffic_group][period]

            result[traffic_group][1] = round(result[traffic_group][1], 6)

            if "+" in result[traffic_group][0]:
                result[traffic_group][0] += f" = {result[traffic_group][1]}"

        return result

    def generate_calculation(self):
        self.deltas = self.generate_deltas_calculation()

        for traffic_group in self.traffic_groups:
            self.result[traffic_group] = ["", 0.0]

            self.result[traffic_group][0] += f"{self.start_balances[traffic_group]}"
            self.result[traffic_group][1] += self.start_balances[traffic_group]

            if self.profits[traffic_group] >= 0:
                self.result[traffic_group][0] += f" + {self.profits[traffic_group]}"
            else:
                self.result[traffic_group][0] += f" - {-self.profits[traffic_group]}"

            self.result[traffic_group][1] += self.profits[traffic_group]

            self.result[traffic_group][0] += f" + {self.deltas[traffic_group][1]}"
            self.result[traffic_group][1] += self.deltas[traffic_group][1]

            if self.tests[traffic_group][1] > 0:
                self.result[traffic_group][0] += f" + {self.tests[traffic_group][1]}"
                self.result[traffic_group][1] += self.tests[traffic_group][1]

            if self.result[traffic_group][1] >= 0:
                self.result[traffic_group][1] *= self.final_percents[traffic_group]
                self.result[traffic_group][1] = round(self.result[traffic_group][1], 6)
                self.result[traffic_group][0] = (
                    f"({self.result[traffic_group][0]}) * {self.final_percents[traffic_group]}"
                    f" = {self.result[traffic_group][1]}")
            else:
                self.result[traffic_group][1] = round(self.result[traffic_group][1], 6)
                self.result[traffic_group][0] += f" = {self.result[traffic_group][1]}"
