# no shebang
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from math import floor
from algo2.pos_sizers.base_sizer import AbstractPositionSizer


class LiquidateRebalancePositionSizer(AbstractPositionSizer):
    """
    Carries out a periodic full liquidation and rebalance of
    the Portfolio.

    This is achieved by determining whether an order type type
    is "EXIT" or "BOT/SLD".

    If the former, the current quantity of shares in the ticker
    is determined and then BOT or SLD to net the position to zero.

    If the latter, the current quantity of shares to obtain is
    determined by prespecified weights and adjusted to reflect
    current account equity.
    """
    def __init__(self, ticker_weights):
        self.ticker_weights = ticker_weights  # NB: this is dict, e.g. ={'GOOG': 0.1, ...}

    def size_order(self, portfolio, initial_order):
        """
        Size the order to reflect the dollar-weighting of the
        current equity account size based on pre-specified ticker weights.
        """
        ticker = initial_order.ticker
        if initial_order.action == "EXIT":
            # Obtain current quantity and liquidate
            cur_quantity = portfolio.positions[ticker].quantity
            if cur_quantity > 0:
                initial_order.action = "SLD"
                initial_order.quantity = cur_quantity
            elif cur_quantity < 0:
                initial_order.action = "BOT"
                initial_order.quantity = cur_quantity
            else:
                initial_order.quantity = 0
        else:
            weight = self.ticker_weights[ticker]
            # Determine total portfolio value, work out dollar weight
            # and finally determine integer quantity of shares to purchase
            close_price = portfolio.data_handler.tickers[ticker]["adj_close"]
            dollar_weight = weight * portfolio.equity
            weighted_quantity = int(floor(dollar_weight / close_price))
            # Update quantity
            initial_order.quantity = weighted_quantity
        return initial_order
