import sys


def progress(count, total, suffix=''):
    if total == 0:
        print("\r\n")
        return

    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '' \
          '|' * filled_len + ' ' * (bar_len - filled_len)

    sys.stdout.write('\r[%s] %s%s ...%s' % (bar, percents, '%', suffix))
    sys.stdout.flush()  # As suggested by Rom Ruben

