import random
import argparse
from enum import Enum
import datetime as dt
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('filepath', type=str, help='path to the xml data from duke-energy')
args = parser.parse_args()

# Season date windows
DFLT_YEAR = 1  # value here doesn't matter but it is constant so we can compare dates without year
WINTER_DATE_START = dt.date(DFLT_YEAR, 5, 1)
WINTER_DATE_END = dt.date(DFLT_YEAR, 9, 30)
SUMMER_DATE_START = dt.date(DFLT_YEAR, 10, 1)
SUMMER_DATE_END = dt.date(DFLT_YEAR, 4, 30)

# Season time windows for peak pricing
WINTER_PEAK_TIME_START = dt.time(hour=6)
WINTER_PEAK_TIME_END = dt.time(hour=9)
WINTER_DISCOUNT_TIME_START1 = dt.time(hour=1)
WINTER_DISCOUNT_TIME_END1 = dt.time(hour=3)
WINTER_DISCOUNT_TIME_START2 = dt.time(hour=11)
WINTER_DISCOUNT_TIME_END2 = dt.time(hour=16)
SUMMER_PEAK_TIME_START = dt.time(hour=18)
SUMMER_PEAK_TIME_END = dt.time(hour=21)
SUMMER_DISCOUNT_TIME_START = dt.time(hour=1)
SUMMER_DISCOUNT_TIME_END = dt.time(hour=6)
CRITICAL_RATE = 20. / 365.  # 20 days a year. Same time period as peak times


def main():
    # the rate models to try
    residential_rates = {
        RateType.OFF_PEAK: 0.11661
    }

    tou_rates = {
        RateType.OFF_PEAK: 0.10467,
        RateType.ON_PEAK: 0.27653,
        RateType.DISCOUNT: 0.06814,
    }

    toucpp_rates = {
        RateType.OFF_PEAK: 0.10289,
        RateType.ON_PEAK: 0.20533,
        RateType.DISCOUNT: 0.07740,
        RateType.CRITICAL: 0.38351,
    }

    # calculate and print
    times, kwhs = read_duke_xml(args.filepath)

    res_cost = calculate_total_cost(residential_rates, times, kwhs)
    tou_cost = calculate_total_cost(tou_rates, times, kwhs)
    toucpp_cost = calculate_total_cost(
        toucpp_rates, times, kwhs, critical_rates=True)
    costs = [('residential', res_cost), ('time-of-use', tou_cost),
             ('time-of-use-cpp', toucpp_cost)]

    print(
        f"The cost for {round(sum(kwhs),2)} kwhs spanning {times[0].date()} to {times[-1].date()}:")
    for name, cost in costs:
        print("\t{:>15}: ${}".format(name, cost))


class RateType(Enum):
    OFF_PEAK = 0
    ON_PEAK = 1
    DISCOUNT = 2
    CRITICAL = 3


def read_duke_xml(filename, start_date=dt.date.min, end_date=dt.date.max):
    namespaces = {
        'ns3': 'http://www.w3.org/2005/Atom',
        'espi': 'http://naesb.org/espi'
    }

    tree = ET.parse(filename)
    root = tree.getroot()

    # Parse the xml to extract timestamp and kwh value
    times = []
    kwhs = []
    for ir in root.findall('ns3:content/espi:IntervalBlock/espi:IntervalReading', namespaces):
        t = ir.find('espi:timePeriod', namespaces).find(
            'espi:start', namespaces).text
        t = dt.datetime.fromtimestamp(int(t))
        if start_date <= t.date() <= end_date:
            times.append(t)
            kwhs.append(float(ir.find('espi:value', namespaces).text))

    return times, kwhs


def get_kwhs_timeperiod(start_date, end_date):
    times, kwhs = read_duke_xml('energy_usage.xml', start_date, end_date)
    return times, kwhs


def is_peak_time(dt):
    tmpdate = dt.date().replace(year=DFLT_YEAR)
    if SUMMER_DATE_START <= tmpdate <= SUMMER_DATE_END:
        return SUMMER_PEAK_TIME_START <= dt.time() <= SUMMER_PEAK_TIME_END
    else:  # winter
        return WINTER_PEAK_TIME_START <= dt.time() <= WINTER_PEAK_TIME_END


def is_discount_time(dt):
    tmpdate = dt.date().replace(year=DFLT_YEAR)
    if SUMMER_DATE_START <= tmpdate <= SUMMER_DATE_END:
        return SUMMER_DISCOUNT_TIME_START <= dt.time() <= SUMMER_DISCOUNT_TIME_END
    else:  # winter
        return WINTER_DISCOUNT_TIME_START1 <= dt.time() <= WINTER_DISCOUNT_TIME_END1 or \
            WINTER_DISCOUNT_TIME_START2 <= dt.time() <= WINTER_DISCOUNT_TIME_END2


def calculate_total_cost(rates, datetimes, kwhs, critical_rates=False):
    # if including critical rates, take average of multiple runs for critical period randomness
    iterations = 10 if critical_rates else 1
    costs = []
    for i in range(iterations):
        cost = sum([get_cost(rates, datetimes[i], kwhs[i], critical_rates)
                    for i in range(len(datetimes))])
        costs.append(cost)
    return round(sum(costs)/len(costs), 2)


def get_cost(rates, datetime, kwh, critical_rates=False):
    if is_peak_time(datetime) and RateType.ON_PEAK in rates:
        if critical_rates and RateType.CRITICAL in rates and random.random() < CRITICAL_RATE:
            return rates[RateType.CRITICAL]*kwh
        return rates[RateType.ON_PEAK]*kwh
    elif is_discount_time(datetime) and RateType.DISCOUNT in rates:
        return rates[RateType.DISCOUNT]*kwh

    return rates[RateType.OFF_PEAK]*kwh


if __name__ == "__main__":
    main()
