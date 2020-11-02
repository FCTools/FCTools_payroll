
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

    def generate_pdf(self):
        pass

    def generate_deltas_calculation(self):
        result = {}

        for traffic_group in self.traffic_groups:
            result[traffic_group] = ["", 0.0]

            for period in self.deltas[traffic_group]:
                if result[traffic_group][0]:
                    result[traffic_group][0] += f" + {self.deltas[traffic_group][period]} [{period}]"
                else:
                    result[traffic_group][0] += f"{self.deltas[traffic_group][period]} [{period}]"
                result[traffic_group][1] += self.deltas[traffic_group][period]

            if "+" in result[traffic_group][0]:
                result[traffic_group][0] += f" = {result[traffic_group][1]}"

        return result

    def generate_calculation(self):
        result = {}
        self.deltas = self.generate_deltas_calculation()

        for traffic_group in self.traffic_groups:
            result[traffic_group] = ["", 0.0]

            result[traffic_group][0] += f"{self.start_balances[traffic_group]}"
            result[traffic_group][1] += self.start_balances[traffic_group]

            result[traffic_group][0] += f" + {self.deltas[traffic_group][1]}"
            result[traffic_group][1] += self.deltas[traffic_group][1]

            result[traffic_group][0] += f" + {self.deltas[traffic_group][1]}"
            result[traffic_group][1] += self.deltas[traffic_group][1]

            if self.tests[traffic_group][1] > 0:
                result[traffic_group][0] += f" + {self.tests[traffic_group][1]}"
                result[traffic_group][1] += self.tests[traffic_group][1]

            if result[traffic_group][1] > 0:
                result[traffic_group][0] = f"({result[traffic_group][0]}) * {self.final_percents[traffic_group]} = " \
                                           f"{result[traffic_group][1] * self.final_percents[traffic_group]}"
