from abc import ABCMeta, abstractmethod
from six import add_metaclass
import re

METRIC_NAME_PREFIX = "KernelMetric"


class KernelMetricStore(ABCMeta):
    """
    KernelMetricStore Is acting as a store of all the metric classes created using KernelMetric base class.
    TYPES is a dictionary that maps the names of the metrics to the metric classes themselves.

    Additionally it defines defines a standard for how kernel metric classes should be named.
    Example:
    If the name of the class that exposes a metric is "KernelMetricMemoryUsage",
    the dictionary will remove the must have prefix "KernelMetric",
    split the rest by camel case letters with a "_" delimiter, and then turn them all to lower case.
    the name that maps to the class of the metric will be "memory_usage".

    *ALL KERNEL METRIC CLASSES MUST INHERIT FROM THE BASE CLASS `KernelMetric`
    *ALL KERNEL METRIC CLASSES MUST HAVE THE PREFIX IN THEIR NAME

    When we define a metric class to inherit from the `KernelMetric`, this class will automatically
    check that its name has the need prefix, and will add it to the TYPES dict.
    """
    TYPES = {}

    def __new__(mcs, name, bases, dct):
        mcs._check_name_prefix(mcs, name)
        new_metric_class = super(KernelMetricStore, mcs).__new__(mcs, name, bases, dct)
        if new_metric_class.__name__ == "KernelMetric":
            return new_metric_class
        mcs._add_new_metric(mcs, new_metric_class)
        return new_metric_class

    def _add_new_metric(self, new_metric):
        metric_name = new_metric.__name__[len(METRIC_NAME_PREFIX):]
        metric_name = re.sub('(?!^)([A-Z][a-z]+)', r' \1', metric_name).split()
        metric_name = "_".join(metric_name).lower()
        self.TYPES[metric_name] = new_metric

    def _check_name_prefix(self, name):
        assert name.startswith(METRIC_NAME_PREFIX)


@add_metaclass(KernelMetricStore)
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

