# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from abc import ABCMeta, abstractmethod


class AbstractPositionRefiner(object):
    """
    The AbstractPositionRefiner abstract class lets the
    sized order through, creates the corresponding
    OrderEvent object and adds it to a list.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def refine_orders(self, portfolio, sized_order):
        raise NotImplementedError("Should implement refine_orders()")
