import os
import time
import datetime
import jwt
import requests
import argparse


"""
In this section, we define the helper functions to access the WindBorne API
This is described in https://windbornesystems.com/docs/api
"""


def wb_get_request(url):
    """
    Make a GET request to WindBorne, authorizing with WindBorne correctly
    """

    client_id = os.environ['WB_CLIENT_ID']  # Make sure to set this!
    api_key = os.environ['WB_API_KEY']  # Make sure to set this!

    # create a signed JSON Web Token for authentication
    # this token is safe to pass to other processes or servers if desired, as it does not expose the API key
    signed_token = jwt.encode({
        'client_id': client_id,
        'iat': int(time.time()),
    }, api_key, algorithm='HS256')

    # make the request, checking the status code to make sure it succeeded
    response = requests.get(url, auth=(client_id, signed_token))

    retries = 0
    while response.status_code == 502 and retries < 5:
        print("502 Bad Gateway, sleeping and retrying")
        time.sleep(2**retries)
        response = requests.get(url, auth=(client_id, signed_token))
        retries += 1

    response.raise_for_status()

    # return the response body
    return response.json()


"""
In this section, we have the core functions to convert data to little_r
"""

def convert_to_little_r(point, output_file='export.little_r'):
    def format_value(value, fortran_format):
        if fortran_format[0] == 'F':
            length, decimal_places = fortran_format[1:].split('.')
            if value is None or value == '':
                return ' ' * int(length)

            # turn into a string of length characters, with decimal_places decimal places
            return f"{value:>{length}.{decimal_places}f}"[:int(length)]

        if fortran_format[0] == 'I':
            length = int(fortran_format[1:])
            if value is None or value == '':
                return ' ' * length

            return f"{value:>{length}d}"[:int(length)]

        if fortran_format[0] == 'A':
            length = int(fortran_format[1:])
            if value is None:
                return ' ' * length

            return str(value)[:length].ljust(length, ' ')

        if fortran_format[0] == 'L':
            if value and value in ['T', 't', 'True', 'true', '1', True]:
                value = 'T'
            else:
                value = 'F'

            length = int(fortran_format[1:])

            return value.rjust(length, ' ')

        raise ValueError(f"Unknown format: {fortran_format}")

    observation_time = datetime.datetime.fromtimestamp(point['timestamp'], tz=datetime.timezone.utc)

    header = ''.join([
        # Latitude: F20.5
        format_value(point.get('latitude'), 'F20.5'),

        # Longitude: F20.5
        format_value(point.get('longitude'), 'F20.5'),

        # ID: A40
        format_value(point.get('id'), 'A40'),

        # Name: A40
        format_value(point.get('mission_name'), 'A40'),

        # Platform (FM‑Code): A40
        format_value('FM-35 TEMP', 'A40'),

        # Source: A40
        format_value('WindBorne', 'A40'),

        # Elevation: F20.5
        format_value('', 'F20.5'),

        # Valid fields: I10
        format_value(-888888, 'I10'),

        # Num. errors: I10
        format_value(0, 'I10'),

        # Num. warnings: I10
        format_value(0, 'I10'),

        # Sequence number: I10
        format_value(0, 'I10'),

        # Num. duplicates: I10
        format_value(0, 'I10'),

        # Is sounding?: L
        format_value('T', 'L10'),

        # Is bogus?: L
        format_value('F', 'L10'),

        # Discard?: L
        format_value('F', 'L10'),

        # Unix time: I10
        # format_value(point['timestamp'], 'I10'),
        format_value(-888888, 'I10'),

        # Julian day: I10
        format_value(-888888, 'I10'),

        # Date: A20 YYYYMMDDhhmmss
        format_value(observation_time.strftime('%Y%m%d%H%M%S'), 'A20'),

        # SLP, QC: F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

        # Ref Pressure, QC: F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

        # Ground Temp, QC: F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

        # SST, QC: F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

        # SFC Pressure, QC: F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

        # Precip, QC: F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

        # Daily Max T, QC: F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

        # Daily Min T, QC: F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

        # Night Min T, QC: F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

        # 3hr Pres Change, QC: F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

        # 24hr Pres Change, QC: F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

        # Cloud cover, QC: F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

        # Ceiling, QC: F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),

        # Precipitable water, QC (see note): F13.5, I7
        format_value(-888888.0, 'F13.5') + format_value(0, 'I7'),
    ])

    pressure_hpa = point.get('pressure')
    pressure_pa = pressure_hpa * 100.0 if pressure_hpa is not None else -888888.0

    temperature_c = point.get('temperature')
    temperature_k = temperature_c + 273.15 if temperature_c is not None else -888888.0

    data_record = ''.join([
        # Pressure (Pa): F13.5
        format_value(pressure_pa, 'F13.5'),

        # QC: I7
        format_value(0, 'I7'),

        # Height (m): F13.5
        format_value(point.get('altitude'), 'F13.5'),

        # QC: I7
        format_value(0, 'I7'),

        # Temperature (K): F13.5
        format_value(temperature_k, 'F13.5'),

        # QC: I7
        format_value(0, 'I7'),

        # Dew point (K): F13.5
        format_value(-888888.0, 'F13.5'),

        # QC: I7
        format_value(0, 'I7'),

        # Wind speed (m/s): F13.5
        format_value(-888888.0, 'F13.5'),

        # QC: I7
        format_value(0, 'I7'),

        # Wind direction (deg): F13.5
        format_value(-888888.0, 'F13.5'),

        # QC: I7
        format_value(0, 'I7'),

        # Wind U (m/s): F13.5
        format_value(point.get('speed_u'), 'F13.5'),

        # QC: I7
        format_value(0, 'I7'),

        # Wind V (m/s): F13.5
        format_value(point.get('speed_v'), 'F13.5'),

        # QC: I7
        format_value(0, 'I7'),

        # Relative humidity (%): F13.5
        format_value(point.get('humidity'), 'F13.5'),

        # QC: I7
        format_value(0, 'I7'),

        # Thickness (m): F13.5
        format_value(-888888.0, 'F13.5'),

        # QC: I7
        format_value(0, 'I7')
    ])

    end_record = '-777777.00000      0-777777.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0'

    tail_record = '     39      0      0'

    lines = [
        header,
        data_record,
        end_record,
        tail_record
    ]

    in_little_r = '\n'.join(lines)

    with open(output_file, 'w') as f:
        f.write(in_little_r)

    return in_little_r


"""
In this section, we tie it all together, querying the WindBorne API and converting it to little_r
"""

def output_data(accumulated_observations, mission_name, starttime, bucket_hours):
    accumulated_observations.sort(key=lambda x: x['timestamp'])

    # Here, set the earliest time of data to be the first observation time, then set it to the most recent
    #    start of a bucket increment.
    # The reason to do this rather than using the input starttime, is because sometimes the data
    #    doesn't start at the start time, and the underlying output would try to output data that doesn't exist
    #
    accumulated_observations.sort(key=lambda x: x['timestamp'])
    earliest_time = accumulated_observations[0]['timestamp']
    if (earliest_time < starttime):
        print("WTF, how can we have gotten data from before the starttime?")
    curtime = earliest_time - earliest_time % (bucket_hours * 60 * 60)

    start_index = 0
    for i in range(len(accumulated_observations)):
        if accumulated_observations[i]['timestamp'] - curtime > bucket_hours * 60 * 60:
            segment = accumulated_observations[start_index:i]
            mt = datetime.datetime.fromtimestamp(curtime, tz=datetime.timezone.utc)+datetime.timedelta(hours=bucket_hours/2)
            output_file = (f"WindBorne_%s_%04d-%02d-%02d_%02d:00_%dh.little_r" %
                           (mission_name, mt.year, mt.month, mt.day, mt.hour, bucket_hours))

            convert_to_little_r(segment, output_file)

            start_index = i
            curtime += datetime.timedelta(hours=bucket_hours).seconds

    # Cover any extra data within the latest partial bucket
    segment = accumulated_observations[start_index:]
    mt = datetime.datetime.fromtimestamp(curtime, tz=datetime.timezone.utc) + datetime.timedelta(hours=bucket_hours / 2)
    output_file = (f"WindBorne_%s_%04d-%02d-%02d_%02d:00_%dh.little_r" %
                   (mission_name, mt.year, mt.month, mt.day, mt.hour, bucket_hours))
    convert_to_little_r(segment, output_file)


def main():
    """
    Queries WindBorne API for data from the input time range and converts it to little_r
    :return:
    """

    parser = argparse.ArgumentParser(description="""
    Retrieves WindBorne data and output to little_r.
    
    Files will be broken up into time buckets as specified by the --bucket_hours option, 
    and the output file names will contain the time at the mid-point of the bucket. For 
    example, if you are looking to have files centered on say, 00 UTC 29 April, the start time
    should be 3 hours prior to 00 UTC, 21 UTC 28 April.
    """, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("times", nargs='+',
                        help='Starting and ending times to retrieve obs.  Format: YY-mm-dd_HH:MM '
                             'Ending time is optional, with current time used as default')
    args = parser.parse_args()

    if len(args.times) == 1:
        starttime=int(datetime.datetime.strptime(args.times[0], '%Y-%m-%d_%H:%M').
                      replace(tzinfo=datetime.timezone.utc).timestamp())
        endtime=int(datetime.datetime.now().timestamp())
    elif len(args.times) == 2:
        starttime=int(datetime.datetime.strptime(args.times[0], '%Y-%m-%d_%H:%M').
                      replace(tzinfo=datetime.timezone.utc).timestamp())
        endtime=int(datetime.datetime.strptime(args.times[1], '%Y-%m-%d_%H:%M').
                    replace(tzinfo=datetime.timezone.utc).timestamp())
    else:
        print("error processing input args, one or two arguments are needed")
        exit(1)

    if (not "WB_CLIENT_ID" in os.environ) or (not "WB_API_KEY" in os.environ) :
        print("  ERROR: You must set environment variables WB_CLIENT_ID and WB_API_KEY\n"
              "  If you don't have a client ID or API key, please contact WindBorne.")
        exit(1)

    args = parser.parse_args()

    observations_by_mission = {}
    accumulated_observations = []
    has_next_page = True

    next_page = f"https://sensor-data.windbornesystems.com/api/v1/super_observations.json?include_ids=true&min_time={starttime}&max_time={endtime}&include_mission_name=true"

    while has_next_page:
        # Note that we query superobservations, which are described here:
        # https://windbornesystems.com/docs/api#super_observations
        # We find that for most NWP applications this leads to better performance than overwhelming with high-res data
        observations_page = wb_get_request(next_page)
        has_next_page = observations_page["has_next_page"]
        if len(observations_page['observations']) == 0:
            print("Could not find any observations for the input date range")

        if has_next_page:
            next_page = observations_page["next_page"]+"&include_mission_name=true&include_ids=true&min_time={}&max_time={}".format(starttime,endtime)

        print(f"Fetched page with {len(observations_page['observations'])} observation(s)")
        for observation in observations_page['observations']:
            if 'mission_name' not in observation:
                print("Warning: got an observation without a mission name")
                continue
                
            if observation['mission_name'] not in observations_by_mission:
                observations_by_mission[observation['mission_name']] = []

            observations_by_mission[observation['mission_name']].append(observation)
            accumulated_observations.append(observation)

            # alternatively, you could call `time.sleep(60)` and keep polling here
            # (though you'd have to move where you were calling convert_to_little_r)


    if len(observations_by_mission) == 0:
        print("No observations found")
        return

    for mission_name, accumulated_observations in observations_by_mission.items():
        for point in accumulated_observations:
            output_dir = os.path.join('data', mission_name)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            output_file = os.path.join(output_dir, f"{point['id']}.little_r")
            convert_to_little_r(point, output_file)


if __name__ == '__main__':
    main()
