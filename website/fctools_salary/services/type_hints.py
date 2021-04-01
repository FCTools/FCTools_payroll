# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of FCTools_payroll
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

from typing import List, Dict, Union

from fctools_salary.domains.tracker.campaign import Campaign

CampaignTracker = Dict[str, Union[Campaign, List]]
