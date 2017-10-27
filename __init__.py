#This file is part of the account_coop_ar module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.

from trytond.pool import Pool
from . import account


def register():
    Pool.register(
        account.PrintChartAccountStart,
        module='account_coop_ar', type_='model')
    Pool.register(
        account.PrintChartAccount,
        module='account_coop_ar', type_='wizard')
    Pool.register(
        account.ChartAccount,
        module='account_coop_ar', type_='report')
