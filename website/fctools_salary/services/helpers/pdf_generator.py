"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import os
from copy import copy
from uuid import uuid4

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table


class PDFGenerator:
    """
    Service for pdf-report with calculation generating.
    """

    @staticmethod
    def _check_saving_path():
        """
        Directory for reports is media/reports.
        This method check this path existing and create it, if it doesn't exist.

        :return: None
        """
        if not os.path.exists("media"):
            os.mkdir("media")
            os.mkdir(os.path.join("media", "reports"))
        elif not os.path.exists(os.path.join("media", "reports")):
            os.mkdir(os.path.join("media", "reports"))

    @staticmethod
    def generate_report(
            total_revenue,
            final_percent,
            start_balances,
            profits,
            from_prev_period,
            tests,
            from_other_users,
            result,
            user,
            start_date,
            end_date,
    ):
        """
        Generates pdf report with result table and returns report's filename.

        :param total_revenue: Total revenue per period.
        :type total_revenue: float

        :param final_percent: final percent (depends on total revenue per period)
        :type final_percent: float

        :param start_balances: user's start balances from database split by traffic sources
        :type start_balances: Dict[str, float]

        :param profits: user's profits from tracker for this period split by traffic sources
        :type profits: Dict[str, float]

        :param from_prev_period: user's deltas from previous period split by traffic sources
        :type from_prev_period: Dict[str, List[Union[str, float]]]

        :param tests: tests calculation split by traffic sources
        :type tests: Dict[str, List[Union[str, float]]]

        :param from_other_users: user's profit from other users (only for teamleads)
        :type from_other_users: Dict[str, List[Union[str, float]]]

        :param result: final calculation
        :type result: Dict[str, List[Union[str, float]]]

        :param user: user
        :type user: User

        :param start_date: period start date
        :type start_date: date

        :param end_date: period end date
        :type end_date: date

        :return: generated report filename
        :rtype: str
        """

        def colored_value(value):
            if value > 0:
                return f"<font color=green>{value}</font>"
            elif value < 0:
                return f"<font color=red>{value}</font>"

            return str(value)

        PDFGenerator._check_saving_path()

        # reports filenames are randomly generated UUID4 (for safety)
        report_filename = os.path.join("media", "reports", f"{uuid4()}.pdf")

        pdf = SimpleDocTemplate(report_filename, pagesize=landscape(A4), )

        meta_content = [
            Paragraph(f"<b>User:</b> {user}", style=settings.PARAGRAPH_STYLE_FONT_12),
            Spacer(height=7, width=600),
            Paragraph(f"<b>Period:</b> {start_date} - {end_date}",
                      style=settings.PARAGRAPH_STYLE_FONT_12),
            Spacer(height=7, width=600),
            Paragraph(f"<b>Total revenue:</b> {total_revenue}",
                      style=settings.PARAGRAPH_STYLE_FONT_12),
            Spacer(height=7, width=600),
            Paragraph(f"<b>Percent:</b> {final_percent}", style=settings.PARAGRAPH_STYLE_FONT_12),
            Spacer(height=7, width=600),
        ]

        start_balances_data = ["Start balance"]
        profits_data = ["Profit"]
        previous_period_data = ["Previous periods"]
        tests_data = ["Tests"]
        from_other_users_data = ["From other users"]
        summary_data = ["Summary"]

        for traffic_group in start_balances:
            start_balances_data.append(Paragraph(colored_value(start_balances[traffic_group]),
                                                 style=settings.PARAGRAPH_STYLE_FONT_11))
            profits_data.append(Paragraph(colored_value(profits[traffic_group]),
                                          style=settings.PARAGRAPH_STYLE_FONT_11))
            previous_period_data.append(Paragraph(from_prev_period[traffic_group],
                                                  style=settings.PARAGRAPH_STYLE_FONT_11))
            tests_count_string = tests[traffic_group][0] \
                .replace(f' = {tests[traffic_group][1]}', f' = <font color=green>{tests[traffic_group][1]}</font>')
            tests_data.append(Paragraph(copy(tests_count_string), style=settings.PARAGRAPH_STYLE_FONT_11))

            if user.is_lead:
                from_other_users_data.append(
                    Paragraph(from_other_users[traffic_group][0], style=settings.PARAGRAPH_STYLE_FONT_11))

            colored_total_amount = colored_value(result[traffic_group][1])
            summary_data.append(Paragraph(copy(result[traffic_group][0].replace(f' = {result[traffic_group][1]}',
                                                                                f' = {colored_total_amount}')),
                                          style=settings.PARAGRAPH_STYLE_FONT_11))

        data = [["--------"] + [traffic_group for traffic_group in result],
                start_balances_data,
                profits_data,
                previous_period_data,
                tests_data, ]

        if user.is_lead:
            data.append(from_other_users_data)
        data.append(summary_data)

        cols_number = len(result)
        col_widths = [120] + [650 // cols_number for _ in range(cols_number)]
        row_heights = [25, 25, 25, 50, 200]

        if user.is_lead:
            row_heights.append(50)
        row_heights.append(25)

        result_table = Table(data, colWidths=col_widths, rowHeights=row_heights)

        result_table.setStyle(settings.TABLE_STYLE)

        footer = [Spacer(width=600, height=15),
                  Paragraph("© FC Tools 2020",
                            style=ParagraphStyle(name="style", alignment=1, textColor=colors.darkgray))]

        pdf.build([*meta_content, result_table, *footer])

        return report_filename
