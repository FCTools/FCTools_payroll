"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

from typing import List, Dict, Union

from fctools_salary.domains.tracker.campaign import Campaign

CampaignTracker = Dict[str, Union[Campaign, List]]
