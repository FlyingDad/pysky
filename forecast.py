import dwml

_hourly_params = { 'snow': 'snow', 'temp': 'temp', 'humidity': 'rhm', 'precip': 'pop12',
     'sky': 'sky', 'weather': 'wx', 'symbol': 'sym', 'wind_gust': 'wgust', 'wind_sustained': 'wspd'}

def process_xml(xml, include_hourly = False):
    """
    Process XML string and return forecast data
    
    args:
        xml - XML string
        include_hourly - Include hourly forecast

    returns: dictionary, see README
    """
    # Parse DWML into python object
    xml_data = dwml.parse_xml(xml)

    print(xml_data)
    return
    return {'daily': _daily(xml_data), 'hourly': _hourly(xml_data)}
    #self._cleanup()

def _daily(xml_data):

    daily_data = []

    # Organize data by date
    #   Format will be tmp_data with date as keys
    #       tmp_data[*date*][*code*] = {values: [*vals*], startDate: *startDate*, endDate: *endDate*}
    tmp_data = {}
    for code in xml_data:
        for val_data in xml_data[code]['values']:
            date = val_data['startDate'] # Use start date as daily date
            if date not in xml_data:
                tmp_data[date] = {}
                daily_data[date] = {}
            if code not in xml_data[date]:
                tmp_data[date][code] = []
            tmp_data[date][code].append(val_data)

    # Parsing configuration
    # Includes:
    #   DWML NOAA code - required
    #   aggregator: determines how to aggregate the data - required
    #   pre-filter: method that takes values as arguments and returns values that should be aggregated
    #   formatter: method that applies formatting to resulting aggregated value
    config = {
        'high': {'code': 'maxt', 'aggregator': _first},
        'precip_day': {'code': 'pop12', 'aggregator': _first, 'pre_filter': _pre_precip_day},
        'precip_night': {'code': 'pop12', 'aggregator': _first, 'pre_filter': _pre_precip_night},
        'rain_amount': {'code': 'qpf', 'aggregator': sum, 'pre_filter': _pre_rain_amount, 'formatter': _format_precip},
        'snow_amount': {'code': 'qpf', 'aggregator': sum, 'pre_filter': _pre_snow_amount, 'formatter': _format_precip},
        'relative_humidity': {'code': 'rhm', 'aggregator': _average},
        'wind_gust': {'code': 'wgust', 'aggregator': max, 'formatter': _format_wind},
        'wind_sustained': {'code': 'wspd', 'aggregator': _average, 'formatter': _format_wind},
        'weather': {'code': 'wx', 'aggregator': _first_nonempty, 'pre_filter': _pre_weather, 'formatter': _format_weather},
        'wsym': {'code': 'sym', 'aggregator': _frequent, 'pre_filter': _pre_wsym, 'formatter': _format_wsym}
    }

    # Loop over tmp_data
    for date in tmp_data:
        for key in config:
            code = config[key]['code']
            if code in daily_data[date]:
                daily_data[date][code] = _aggregate_values(
                    code, 
                    aggregators[code],
                    pre_filters[code] if code in pre_filters else None,
                    formatters[code] if code in formatters else None
                )

    return daily_data

    #daily_data[date][code] = _aggregate_values(tmp_data[date][code])
    #data = {} 
    #forecastData['daily'][date][label] = _aggregate(xml_data, 'maxt', 'high', 'first')
    #_dailyLow()
    #_aggregate('pop12', 'precip_day', 'first', skipFunction = self._skipDailyPrecipDay)
    #_aggregae('pop12', 'precip_night', 'first', skipFunction = self._skipDailyPrecipNight)
    #_aggregate('qpf', 'rain_amount', 'sum', True, 2, skipFunction = self._skipRain)
    #_aggregate('snow', 'snow_amount', 'sum', True, 1, skipFunction = self._skipSnow)
    #_aggregate('rhm', 'relative_humidity', 'average')
    #_aggregate('wgust', 'wind_gust', 'max', formatFunction = self._formatWind)
    #_aggregate('wspd',  'wind_sustained', 'average', formatFunction = self._formatWind)
    #_aggregate('wx', 'weather', 'first-nonempty', False, formatFunction = self._formatWeather, 
    #                skipFunction = self._skipDailyWeather)
    #_aggregate('sym', 'wsym', 'frequent', False, formatFunction = self._formatSymbol, 
    #                skipFunction = self._skipDailySymbol)

def _first(values):
    """
    Aggregate by first value
    Arg: values - list of values
    Returns: first value
    """
    return values[0]

def _average(values):

    """
    Aggregate by average value
    Arg: values - list of values
    Returns: average value
    """
    return sum(values)/len(values)

def _first_nonempty(values):
    """
    Aggregate by first non-empty
    Args: values - list of values
    Returns: first non-empty value
    """
    for val in vals:
        if len(val) > 0:
            return val

def _frequent(values):
    """
    Aggregate by most frequently used values
    Args: values - list of values
    Returns: most frequently appearing value
    """
    counts = {}
    for val in vals:
        if not counts.has_key(val):
            counts[val] = 0
        counts[val] = counts[val] + 1
    maxCount = 0
    for k, v in counts.iteritems():
        if v > maxCount:
            val = k
    return val

def _aggregate_values(value_data, aggregator, pre_filter=None, formatter=None):
    """
    Aggregate values using optional filter and format functions

    args:
        values - list of values to aggregate
        pre_filter - filter function
        formatter - format function
    """
    # Apply filter
    values = pre_filter(value_data) if pre_filter else _pre_values(value_data)

    # Aggregate
    val = aggregator(values)

    # Apply formatter
    if formatter:
        val = formatter(values)

    return val

def _pre_values(value_data):
    """
    Convert extra values from value data, which also contains date/time information.  Default pre- filter
    args:
        value_data - array of dictionaries containing value and date data
    returns:
        values - list of values
    """
    return [val['value'] for val in value_data]
       
def _pre_precip_day(value_data):
    """
    Pre- filter function for daily precipitation % that excludes 12-hour precipitation data
        that crosses a date (e.g., start=1/1/12 end=1/2/12)
    """
    return [val['value'] for val in value_data if val['startDate'] == val['endDate']]

def _pre_precip_night(value_data):

    """
    Pre- filter function for nightly precipitation % that excludes 12-hour precipitation data
        that is on the same date (e.g., start=1/1/12 end=1/2/12)
    """
    return [val['value'] for val in value_data if val['startDate'] != val['endDate']]

def _pre_rain_amount(value_data):
    """
    Pre- filter for rain amount
      Removes zero-length values and converts remaining to float and rounds to 2 decimals
    """
    return [round(float(val['value']), 2) for val in value_data if len(val['value'])]

def _pre_snow_amount(value_data):
    """
    Pre- filter for snow amount
        Removes zero-length values and converts remaining to float and rounds to 1 decimal
    """
    return [round(float(val['value']), 1) for val in value_data if len(val['value'])]

def _pre_weather(value_data):
    """
    Pre- filter for weather that skips weather between 6PM and 6AM so we get daytime conditions
    """
    return [val['value'] for val in value_data if val['startTime'] >= '06:00:00' and val['startTime'] <= '18:00:00']

def _pre_wsym(value_data):
    """
    Pre- filter for weather symbols, skips if empty or does not contain path
    """
    return [val['value'] for val in value_data if len(val['value']) and val['value'].find('/') != -1]

def _format_wind(value):
    """
    Format function for wind, convert from knots to MPH
    """
    return "%.1f" % round(float(value) * 1.15077945, 1) if value else '' # convert from knots to MPH

def _format_weather(value):
    """
    Format function for weather
    """
    # Check for format
    if len(value.strip('|').split('|')) < 3:
        return ''

    # Get coverage, intensity and weather type elements
    coverage_element, intensity_element, weather_type_element = value.strip('|').split('|')[0:3]

    # Get coverage from coverage element
    coverage = coverage_element.split(':')[1]

    # Get intensity from intensity element
    intensity = intensity_element.split(':')[1]
    if intensity == 'none':
        intensity = ''

    weather = weather_type_element.split(':')[1]

    str = ''
    if coverage == 'likely':
        str = "%s %s %s" % (intensity, weather, coverage)
    elif coverage == 'chance' or coverage == 'slight chance':
        str = "%s of %s %s" % (coverage, intensity, weather)
    elif coverage == 'definitely':
        str = "%s %s" % (intensity, weather)
    else:
        str = "%s %s %s" % (coverage, intensity, weather)

    return str


def _format_wsym(value):
    """
    Form function for symbols, return only image
    """
    return value.split('/')[-1] if value else ''

# Aggregate 3-hour values using a function
# @param int code Noaa parameter code
# @param string function Name of aggregate function, 'sum', 'average', 'max', 'min'
# @param boolean isNumeric T: value is numeric
# @param int decimal Number of places to round to
# @param function skipFunction Function used to determine if value should be skipped
# @param function formatFunction Function used to format value
# @return null
#def _aggregate(xml_data, code, label, function, isNumeric = True, decimal = 0, 
#                   skipFunction = None, formatFunction = None):
#       
#    # Setup tmpData to store temporary data ??
#    tmpData = {}
#
#    # Loop over the values associated with this parameter
#    #   Initialize tmpData for each date and add values
#    for vData in xml_data[code]['values']:
#           
#        # Get start date and initialize temporary data with start date key
#        startDate = vData['startDate']
#        if startDate not in tmpData:
#            tmpData[startDate] = []
#            
#        # Get value
#        val = vData['value']
#        
#        # Convert to float if this value is supposed to be numeric and has length
#        if isNumeric and len(val) > 0:
#            val = float(val)
#           
#        # Check to see that skip function does not exist, or when applied to value does not get skipped
#        #    Add to tmpData
#        if not skipFunction or not skipFunction(vData):
#            tmpData[startDate].append(val)
#               
#    # Loop over all the dates
#    for date in tmpData:
#           
#        # Initialize date in forecast data
#        #self._initDate(date)
#        if date not in self.forecastData['daily']:
#            self.forecastData['daily'][date] = {}
#       
#        # Get values for date
#        vals = tmpData[date]
#           
#        # If not values for this date, continue
#        if len(vals) == 0:
#                
#            continue
#            
#        # If measuring rain amount and don't have a full 3 data points
#        # May be slightly inaccurate
#        if code in ('qpf', 'snow') and len(vals) < 3:
#                
#            continue
#            
#        # Apply aggregate function
#        if function == 'average':
#            val = sum(vals)/len(vals)
#        elif function == 'sum':
#            val = sum(vals)
#        elif function == 'max':
#            val = max(vals)
#        elif function == 'min':
#            val = min(vals)
#        elif function == 'first':
#            val = vals[0]
#        elif function == 'first-nonempty':
#            for val in vals:
#                if len(val) > 0:
#                    break
#        elif function == 'frequent':
#            counts = {}
#            for val in vals:
#                if not counts.has_key(val):
#                    counts[val] = 0
#                counts[val] = counts[val] + 1
#            maxCount = 0
#            for k, v in counts.iteritems():
#                if v > maxCount:
#                    val = k
#                    maxCount = v
#        else:
#            val = vals[0]
#            
#        if isNumeric:
#            if decimal == 0:
#                val = int(val)
#            else:
#                val = round(val, decimal)
#                
#        if formatFunction:
#            
#            val = formatFunction(val)
#           
#        return val 
#        #self.forecastData['daily'][date][label] = val

# Convert XML date to SQL - TODO - look at what we are doing here with the timezone offset
#def _convert_xml_datetime_sql(xml_date):
#
#    if len(xml_date):
#
#        sql_date, sql_time = xml_date.split('T')
#        #date_str = date_str.replace('-04:00','')
#        sql_time, offset = sql_time.split('-') # do nothing with offset - this is local time
#        hour, minute, second = sql_time.split(':')
#        #offset_hour, offset_minute = offset.split(':')
#        #offset_hour_difference = int(offset_hour) - 4 # Use 4 since this is what our standard was initially - will probably need to change
#        #hour = int(hour)+int(offset_hour_difference)
#        sql_time = "%s:%s:%s" % (hour, minute, second)
#        return sql_date + ' ' + sql_time
#
#    else:
#
#        return ''
