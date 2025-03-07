import time
from copy import deepcopy
from time import sleep

import busypie
from busypie.durations import SECOND, ONE_HUNDRED_MILLISECONDS

_DEFAULT_MAX_WAIT_TIME = 10 * SECOND


class ConditionBuilder:
    def __init__(self, condition=None):
        self._condition = Condition() if condition is None else condition

    def at_most(self, value, unit=SECOND):
        self._condition.wait_time_in_secs = value * unit
        return self._new_builder_with_cloned_condition()

    def _new_builder_with_cloned_condition(self):
        return ConditionBuilder(deepcopy(self._condition))

    def ignore_exceptions(self, *excludes):
        self._condition.ignored_exceptions = excludes
        return self._new_builder_with_cloned_condition()

    def until(self, func):
        ConditionAwaiter(self._condition).wait_for(func)


class Condition:
    wait_time_in_secs = _DEFAULT_MAX_WAIT_TIME
    ignored_exceptions = None


class ConditionAwaiter:
    def __init__(self, condition):
        self._condition = condition

    def wait_for(self, func):
        start_time = time.time()
        while True:
            try:
                if func():
                    break
            except Exception as e:
                self._raise_exception_if_not_ignored(e)
            self._validate_wait_constraint(func.__name__, start_time)
            sleep(ONE_HUNDRED_MILLISECONDS)

    def _raise_exception_if_not_ignored(self, e):
        ignored_exceptions = self._condition.ignored_exceptions
        if ignored_exceptions is None or \
                (ignored_exceptions and e.__class__ not in ignored_exceptions):
            raise e

    def _validate_wait_constraint(self, func_name, start_time):
        if (time.time() - start_time) > self._condition.wait_time_in_secs:
            raise busypie.ConditionTimeoutError("Failed to meet condition of {} within {} seconds"
                                                .format(func_name, self._condition.wait_time_in_secs))


class ConditionTimeoutError(Exception):
    pass
