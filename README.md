# duke-energy-rate-model-calculator
Simple python script for calculating your electric price for different rate models. Duke energy has flat rate models as well as time-of-use models. This will calculate the price you would pay given your past electric use data, which you can download in xml format from duke energy.

You can find the rates here: [https://www.duke-energy.com/home/billing/rates](https://www.duke-energy.com/home/billing/rates).

You can find a description of one of their time-of-use models here: [https://www.duke-energy.com/home/billing/flex-savings-option](https://www.duke-energy.com/home/billing/flex-savings-option).

You can simply run the program as follows:
```python
python calc.py energy_usage_small.xml
```
and the output will look like:
```
The cost for 328.08 kwhs spanning 2023-12-23 to 2023-12-28:
            residential: $38.26
            time-of-use: $40.03
        time-of-use-cpp: $37.19
```

**NOTE:** There are a number of hardcoded things near the top of the code in `calc.py` related to the time windows and rates of the particular models.