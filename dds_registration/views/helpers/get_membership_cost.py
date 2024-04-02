# @module dds_registration/views/helpers/get_membership_cost.py
# @changed 2024.04.02, 14:35

from ...core.constants.payments import membership_cost_by_type

from ...models import Membership


def get_membership_cost(membership: Membership):
    membership_type = membership.membership_type
    cost = membership_cost_by_type[membership_type]
    # TODO: Calculate by membership options?
    return cost
