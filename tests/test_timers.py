import time

from lib.timers import Scheduler


def test_first_check_returns_true_with_default_configure():
    scheduler = Scheduler()
    scheduler.configure('foo', 3)
    assert scheduler.check('foo') is True


def test_checks_time_greater_than_now():
    scheduler = Scheduler()
    scheduler.configure('foo', 3, starts=time.time())
    time.sleep(2)
    assert scheduler.check('foo') is False
    time.sleep(2)
    assert scheduler.check('foo') is True
