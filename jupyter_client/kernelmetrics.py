from abc import ABCMeta, abstractmethod
from six import add_metaclass
import re

METRIC_NAME_PREFIX = "KernelMetric"


class KernelMetricMeta(ABCMeta):
    """
    Meta class for all of the kernel metric classes.
    When defining a class, will check for its name, that it has the
    predefined prefix.
    If not, throws an assertion error.
    """
    def __new__(mcs, name, bases, dct):
        assert name.startswith(METRIC_NAME_PREFIX)
        return super(KernelMetricMeta, mcs).__new__(mcs, name, bases, dct)


@add_metaclass(KernelMetricMeta)
class KernelMetric(object):
    """
    An abstract base class for all of the metric classes.
    """
    def __init__(self, kernel_manager):
        """
        :param kernel_manager: desired kernel to pull the metric from
        """
        self.kernel_manager = kernel_manager

    @abstractmethod
    def poll(self):
        """
        Polls the necessary metric from the kernel and returns it
        :return: Metric data
        """
        pass


class KernelMetricMemoryUsage(KernelMetric):
    """
    Returns memory usage of the kernel in MB.
    `poll` function should be overwritten if there is a
    need for a different kind of implementation.
    """
    def poll(self):
        from psutil import Process
        kernel_pid = self.kernel_manager.kernel.pid
        process = Process(kernel_pid)
        mem = process.memory_info().vms
        return self._bytes_to_mb(mem)

    def _bytes_to_mb(self, num):
        return int(num / 1024 ** 2)


"""
KERNEL_METRIC_TYPES is a dictionary that maps the names of the metrics
to the metric classes themselves.

Example:
If the name of the class that exposes a metric is "KernelMetricMemoryUsage",
the dictionary will remove the must have prefix "KernelMetric", 
split the rest by camel case letters with a "_" delimiter, and then turn them all to lower case.
the name that maps to the class of the metric will be "memory_usage".

*ALL KERNEL METRIC CLASSES MUST BE DEFINED ABOVE, INHERITING FROM THE BASE CLASS `KernelMetric`
*ALL KERNEL METRIC CLASSES MUST HAVE THE PREFIX DEFINED AT THE TOP OF THE FILE
*ALL KERNEL METRIC CLASSES MUST RECEIVE ONLY THE KERNEL MANAGER AS ITS FIRST AND ONLY PARAMETER
*ALL KERNEL METRIC CLASSES MUST DEFINE THE `poll` METHOD THAT RETURNS THE DESIRED METRIC
"""
KERNEL_METRIC_TYPES = {}
for cls in KernelMetric.__subclasses__():
    metric_name = cls.__name__[len(METRIC_NAME_PREFIX):]
    metric_name = re.sub('(?!^)([A-Z][a-z]+)', r' \1', metric_name).split()
    metric_name = "_".join(metric_name).lower()
    KERNEL_METRIC_TYPES[metric_name] = cls



