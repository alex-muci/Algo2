#!/usr/bin/python
# -*- coding: utf-8  -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


from enum import Enum
EventType = Enum("EventType", "TICK BAR SIGNAL ORDER FILL")


class Event(object):
    """
    Event is the base class, provinding an interface
    for all inherited that will be created/stored
    
    @property
    def typename(self):
        return self.type.name
    """
    pass


class MarketEvent(Event):
    """
    Handles the event of receiving a new market update
    and triggers Strategy to generate signals.
    
    Datafeed ->  MarketEvent -> Strategy
    """
    def __init__(self):
        """
        Initialises the MarketEvent.
        """
        self.type = 'MARKET'


class SignalEvent(Event):
    """
    Handles the event of sending a Signal from a Strategy object.
    This is received by a Portfolio object and acted upon.
    Strategy -> SignalEvent -> Portfolio (splittable in sizer and risk mgt)
    """
    def __init__(self, strategy_id, symbol, datetime, signal_type, strength):
        """
        Initialises the SignalEvent.

        Parameters:
        strategy_id - unique ID of the strategy generating the signal.
        symbol - ticker symbol
        datetime - timestamp at which the signal was generated.
        signal_type - either 'LONG' or 'SHORT'.
        strength - adjustment factor "suggestion" used to scale 
            quantity at the portfolio level. Useful for pairs strategies.
        """
        self.strategy_id = strategy_id
        self.type = 'SIGNAL'
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength


class SuggestedOrderEvent(Event):
    """
    A SuggestedOrder object is generated by the PortfolioHandler
    to be sent to the PositionSizer object and subsequently the
    RiskManager object. Creating a separate object type for
    suggested orders and final orders (OrderEvent objects) ensures
    that a suggested order is never transacted unless it has been
    scrutinised by the position sizing and risk management layers.
    """
    def __init__(self, symbol, order_type, quantity=0):
        """
        Initialises the SuggestedOrder. The quantity defaults
        to zero as the PortfolioHandler creates these objects
        prior to any position sizing.

        The PositionSizer object will "fill in" the correct
        value prior to sending the SuggestedOrder to the
        RiskManager.

        Parameters:
        symbol - The ticker symbol, e.g. 'GOOG'.
        order_type - 'BOT' (for long) or 'SLD' (for short)
            or 'EXIT' (for liquidation).
        quantity - The quantity of shares to transact.
        """
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity


class OrderEvent(Event):
    """
    Handles the event of sending an Order to an execution system.
    The order contains a symbol (e.g. GOOG), a type (market or limit),
    quantity and a direction.
    Portfolio -> OrderEvent -> Execution
    """

    def __init__(self, symbol, order_type, quantity, direction):
        """
        Initialises 
        1. order type, either Market order ('MKT') or Limit order ('LMT'), 
        2. quantity (integral) and 
        3. its direction ('BUY' or 'SELL').

        TODO: Must handle error checking here to obtain 
        rational orders (i.e. no negative quantities etc).

        Parameters:
        symbol - The instrument to trade.
        order_type - 'MKT' or 'LMT' for Market or Limit.
        quantity - Non-negative integer for quantity.
        direction - 'BUY' or 'SELL' for long or short.
        """
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction

    def print_order(self):
        """
        Outputs the values within the Order.
        """
        print("Order: Symbol=%s, Type=%s, Quantity=%s, Direction=%s" % 
            (self.symbol, self.order_type, self.quantity, self.direction)
        )


class FillEvent(Event):
    """
    Encapsulates the notion of a Filled Order, as returned
    from a brokerage. Stores the quantity of an instrument
    actually filled and at what price. In addition, stores
    the commission of the trade from the brokerage.
    
    TODO: Currently does not support filling positions at
    different prices. This will be simulated by averaging
    the cost.
    """

    def __init__(self, timeindex, symbol, exchange, quantity, 
                 direction, fill_cost, commission=None):
        """
        Initialises the FillEvent object. Sets the symbol, exchange,
        quantity, direction, cost of fill and an optional 
        commission.

        If commission is not provided, the Fill object will
        calculate it based on the trade size and Interactive
        Brokers fees.

        Parameters:
        timeindex - The bar-resolution when the order was filled (i.e. datetime).
        symbol - The instrument which was filled.
        exchange - The exchange where the order was filled.
        quantity - The filled quantity.
        direction - The direction of fill ('BUY' or 'SELL')
        fill_cost - The holdings value in dollars.
        commission - An optional commission sent from IB.
        """
        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost

        # Calculate commission
        if commission is None:
            self.commission = self.calculate_ib_commission()
        else:
            self.commission = commission

    def calculate_ib_commission(self):
        """
        Calculates the fees of trading based on an Interactive
        Brokers fee structure for API, in USD.

        This does not include exchange or ECN fees.

        Based on "US API Directed Orders":
        https://www.interactivebrokers.com/en/index.php?f=commission&p=stocks2
        """
        full_cost = 1.3
        if self.quantity <= 500:
            full_cost = max(1.3, 0.013 * self.quantity)
        else: # Greater than 500
            full_cost = max(1.3, 0.008 * self.quantity)
        return full_cost
