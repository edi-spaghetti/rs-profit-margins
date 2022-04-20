from django.db import models


class ItemGroup(models.Model):
    """
    Grouping mechanism for item processing of a type.
    For example, all the barrows repairs can be grouped together.
    """
    name = models.CharField(max_length=120)


class Item(models.Model):
    """An internal cache of the OSRS items database."""

    osrs_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=80)


class Process(models.Model):
    """A combination of one or more inputs to produce one or more outputs."""

    name = models.CharField(max_length=120)
    description = models.CharField(max_length=500, null=True, blank=True)
    group = models.ForeignKey(
        ItemGroup,
        on_delete=models.CASCADE,
    )

    @property
    def inputs(self):
        """Return a query list of input items for this process."""
        return self.items.filter(is_input=True)

    @property
    def outputs(self):
        """Return a query list of output items for this process."""
        return self.items.filter(is_input=False)


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
