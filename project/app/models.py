import requests
from uuid import uuid4
from functools import wraps
from time import time

from django.db import models

api_base_url = 'https://prices.runescape.wiki/api/v1/osrs'
agent = f'agent-{uuid4().hex[:8]}'


class ItemGroup(models.Model):
    """
    Grouping mechanism for item processing of a type.
    For example, all the barrows repairs can be grouped together.
    """
    name = models.CharField(max_length=120)


def value_wrapper(func):
    """
    A wrapper for value properties on Item entities.
    Handles updating cache and return special values where appropriate.
    Method must be an instance method with the property decorator.
    """

    @wraps(func)
    def wrapper(self):

        # TODO: error handling on cache update failure
        if self.update_cache():
            print('Updated cache!')

        # special gold pieces item is not in actual cache,
        # and has a fixed price
        if self.osrs_id == -1:
            return 1

        return func(self)
    return wrapper


class Item(models.Model):
    """An internal cache of the OSRS items database."""

    _cache = None
    _cache_timeout = 60  # seconds
    _cache_updated_at = None

    osrs_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=80)

    @classmethod
    def update_cache(cls):

        condition = (
            cls._cache is None
            or cls._cache_updated_at is None
            or (cls._cache_updated_at + cls._cache_timeout < time())
        )
        if not condition:
            return False

        try:
            prices = requests.get(f'{api_base_url}/latest',
                                  headers={'User-Agent': agent})
        except requests.exceptions.ConnectionError:
            return False

        if prices.status_code != 200:
            return False

        # process the incoming data
        prices = prices.json()
        prices = prices.get('data')
        # for some reason item ids come in as strings, fix that
        prices = {int(idx): data for idx, data in prices.items()}

        # cache to class attribute and return
        cls._cache = prices
        cls._cache_updated_at = time()
        return True

    @property
    @value_wrapper
    def low_value(self):
        """
        Get current item's low price from cache.
        """
        data = self._cache.get(self.osrs_id)
        # TODO: error handling if id not found
        return data['low']

    @property
    @value_wrapper
    def high_value(self):
        data = self._cache.get(self.osrs_id)
        # TODO: error handling if id not found
        return data['high']

    @property
    @value_wrapper
    def latest_value(self):
        data = self._cache.get(self.osrs_id)
        if data['highTime'] > data['lowTime']:
            return self.high_value
        else:
            return self.low_value

    @property
    @value_wrapper
    def earliest_value(self):
        data = self._cache.get(self.osrs_id)
        if data['highTime'] < data['lowTime']:
            return self.high_value
        else:
            return self.low_value


class Process(models.Model):
    """A combination of one or more inputs to produce one or more outputs."""

    name = models.CharField(max_length=120)
    description = models.CharField(max_length=500, null=True, blank=True)
    group = models.ForeignKey(
        ItemGroup,
        on_delete=models.CASCADE,
        related_name='processes',
    )

    @property
    def inputs(self):
        """Return a query list of input items for this process."""
        return self.items.filter(is_input=True)

    @property
    def outputs(self):
        """Return a query list of output items for this process."""
        return self.items.filter(is_input=False)

    @property
    def profit(self):
        """
        Calculate the profit generated by doing this process once with all
        items being bought or sold at their latest values
        """
        i_cost = 0
        for i in self.inputs:
            i_cost += i.item.latest_value * i.quantity
        o_cost = 0
        for o in self.outputs:
            o_cost += o.item.latest_value * o.quantity

        return o_cost - i_cost


class ProcessItem(models.Model):
    """An instance of an item used in a process any number of times."""

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='process_items'
    )
    process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        related_name='items'
    )
    quantity = models.IntegerField()
    is_input = models.BooleanField()
