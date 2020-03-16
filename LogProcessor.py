from main import db
from sqlalchemy.orm import sessionmaker
import pandas as pd
from dateutil import parser
from models.Log import Log
from models.LogFailures import LogFailure
from models.IdempotencyCheck import Idempotency
from datetime import datetime

error_codes = {
    300: 'No user_id specified',
    301: 'No session_id specified',
    302: 'No actions array specified',
    304: 'actions array is of size 0',
    305: 'No type provided for the action',
    306: 'No time provided for the action',
    307: 'time parameter incorrectly formatted',
}


def store_idempotency(key):
    if not key:
        return
    idempotency_key = Idempotency(key)
    db.session.add(idempotency_key)
    db.session.commit()


def check_for_repeated_request(key):
    if not key:
        return False

    result = Idempotency.query.filter_by(key=key).first()
    if result:
        return True

    return False


def insert_data(logs):
    db.session.bulk_save_objects(logs)
    db.session.commit()


def check_and_insert_logs(logs_to_insert):
    if len(logs_to_insert) > 10000:
        batch_to_write = logs_to_insert[:10000]
        insert_data(batch_to_write)
        return logs_to_insert[10000:]

    return logs_to_insert


def add_to_dict(dict_to_add, key):
    if key not in dict_to_add:
        dict_to_add[key] = 1
    else:
        dict_to_add[key] += 1


def check_action_body(action):
    type = action.get('type')
    time = action.get('time')

    if not type:
        return 305

    if not time:
        return 306

    try:
        parser.isoparse(time)
    except ValueError:
        return 307

    return 200


def check_log_body(log):
    user_id = log.get('userId')
    session_id = log.get('sessionId')
    actions = log.get('actions')

    if not user_id:
        return 300

    if not session_id:
        return 301

    if not actions:
        return 302

    if not isinstance(actions, list):
        return 303

    if len(actions) == 0:
        return 304

    return 200


def parse_high_level(log):
    return log.get('userId'), log.get('sessionId'), log.get('actions')


def log_builder(action, user_id, session_id):
    action['time'] = parser.isoparse(action['time'])
    return Log(user_id, session_id, action['time'], action['type'], action['properties'])


def build_and_insert_errors(error_counts, error_type):
    log_failures_list = []
    for key in error_counts.keys():
        log_failure = LogFailure(datetime.now(), error_codes[key], error_counts[key], error_type)
        log_failures_list.append(log_failure)

    insert_data(log_failures_list)


def parse_logs_and_write_to_db(request_data):
    logs_json = request_data.get('logs')
    if not logs_json:
        return "Parameter 'logs' not specified as part of POST request, please consult the documentation and try" \
               "again", 400

    log_failures = {}
    for log in logs_json:
        action_failures = {}
        logs_to_insert = []

        log_body_status = check_log_body(log)
        if log_body_status > 200:
            add_to_dict(log_failures, log_body_status)
            continue

        user_id, session_id, actions = parse_high_level(log)
        for action in actions:
            action_body_status = check_action_body(action)
            if action_body_status > 200:
                add_to_dict(action_failures, action_body_status)
                continue

            entry_log = log_builder(action, user_id, session_id)
            logs_to_insert.append(entry_log)
            logs_to_insert = check_and_insert_logs(logs_to_insert)

        if len(logs_to_insert) > 0:
            insert_data(logs_to_insert)

        build_and_insert_errors(action_failures, 'action_error')

    build_and_insert_errors(log_failures, 'log_error')

    return "The logs have successfully been written to the database. Check the log_failures table for any potential " \
           "errors that may have occurred.", 200


def clean_and_collapse_dataframe_to_json(df):
    df.drop_duplicates(subset=['user_id', 'session_id', 'time', 'type'], inplace=True)
    df['time'] = df['time'].map(lambda x: datetime.strftime(x, '%Y-%m-%dT%H:%M:%S+0000'))

    merged_df = df.drop(['time', 'type', 'properties'], axis=1).assign(action_items=
                                                                       df[['time', 'type', 'properties']].agg(
                                                                           pd.Series.to_dict, axis=1))

    logs_df = merged_df.groupby(['user_id', 'session_id'])['action_items'].agg(list)
    logs = []
    for index, row in logs_df.iteritems():
        log_element = {
            'userId': index[0],
            'sessionId': index[1],
            'actions': row
        }

        logs.append(log_element)

    return {'logs': logs}


def build_query_and_get_data(conditions):
    Session = sessionmaker(bind=db.engine)
    session = Session()
    base_query = session.query(Log)

    if conditions.user_id:
        base_query = base_query.filter(Log.userId == conditions.user_id)

    if conditions.type:
        base_query = base_query.filter(Log.type == conditions.type)

    if conditions.timerange:
        timerange = conditions.timerange
        start_range = parser.isoparse(timerange[0])
        end_range = parser.isoparse(timerange[1])

        base_query = base_query.filter(Log.time >= start_range).filter(Log.time <= end_range)

    result_dataframe = pd.read_sql(base_query.statement, session.bind)

    return clean_and_collapse_dataframe_to_json(result_dataframe)


def validate_conditions(conditions):
    timestamp_condition = conditions.timerange
    if timestamp_condition and not isinstance(timestamp_condition, list):
        return "The timerange parameter must be in the form of a list, containing the start and end timestamps", 400

    if timestamp_condition and len(timestamp_condition) != 2:
        return "The timerange parameter must contain two fields: the starting timestamp and the ending timestamp", 400

    if timestamp_condition:
        try:
            start_timestamp = parser.isoparse(timestamp_condition[0])
            end_timestamp = parser.isoparse(timestamp_condition[1])

            if start_timestamp > end_timestamp:
                return "The start_timestamp provided is later than the end_timestamp. " \
                       "Please provide a valid timerange", 400
        except:
            return "The timestamps provided must be of the ISO-8601 standard format.", 400

    return "Valid", 200


def read_logs_from_db(request_data):
    valid_conditions = ['userId', 'type', 'timerange']
    conditions_json = request_data.get('conditions')
    if conditions_json:
        for key in conditions_json.keys():
            if key not in valid_conditions:
                return "Invalid condition(s) provided. The following conditions are permitted: userId, type, timeRange", \
                       400

        conditions = Conditions(conditions_json)
        message, status_code = validate_conditions(conditions)
        if status_code >= 300:
            return message, status_code

        data = build_query_and_get_data(conditions)
        return data, 200

    return "No conditions provided. Please provide at least one.", 400


class Conditions(object):
    def __init__(self, conditions_json):
        self.user_id = conditions_json.get('userId')
        self.timerange = conditions_json.get('timerange')
        self.type = conditions_json.get('type')
