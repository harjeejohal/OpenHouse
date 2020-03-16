# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python37_app]
from flask import Flask, request, jsonify
import LogProcessor

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


@app.route('/read_logs', methods=['POST'])
def read_logs():
    try:
        request_json = request.json
    except Exception as e:
        print(e)
        return "Error occurred while trying to parse the JSON of your request. Please ensure that it's been formatted" \
               " correctly", 400

    try:
        data, statuscode = LogProcessor.read_logs_from_db(request_json)
        if statuscode == 200:
            return jsonify(data), statuscode
        return data, statuscode

    except Exception as e:
        return "Internal Server Error: {}".format(e), 500


@app.route('/write_logs', methods=['POST'])
def write_logs():
    try:
        request_json = request.json
    except Exception as e:
        print(e)
        return "Error occurred while trying to parse the JSON of your request. Please ensure that it's been formatted" \
               " correctly", 400

    try:
        idempotency_key = request_json.get('idempotency_key')
        if LogProcessor.check_for_repeated_request(idempotency_key):
            return "This request has already been processed", 409

        LogProcessor.store_idempotency(idempotency_key)
        return LogProcessor.parse_logs_and_write_to_db(request_json)

    except Exception as e:
        return "Internal Server Error: {}".format(e), 500


@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return 'Hello World!'


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python37_app]
