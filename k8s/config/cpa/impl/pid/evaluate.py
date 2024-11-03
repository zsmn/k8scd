# Copyright 2021 The Custom Pod Autoscaler Authors.
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

import json
import sys
import math
from pid import *
from typing import List

# JSON piped into this script example:
# {
#   "resource": "php-apache",
#   "runType": "api",
#   "metrics": [
#     {
#       "resource": "php-apache",
#       "value": "{\"current_replicas\": 3, \"average_utilization\": 60}"
#     }
#   ]
# }

def main():
    # Parse JSON into a dict
    spec = json.loads(sys.stdin.read())
    evaluate(spec)

def write_last_it_to_file(file_path: str, controller: PIDController):
    with open(file_path, 'w') as file:
        file.write(controller.serialize())

def read_last_it_from_file(file_path: str, default_value: PIDController) -> PIDController:
    try:
        with open(file_path, 'r') as file:
            content = file.read().strip()
            if content == '':
                return default_value.serialize()
            
            return deserialize(content)
    except FileNotFoundError:
        return default_value
    except ValueError:
        return default_value
    except IOError:
        return default_value

def evaluate(spec):
    # Only expect 1 metric provided
    if len(spec["metrics"]) != 1:
        sys.stderr.write("Expected 1 metric")
        exit(1)

    # Get the metric value, there should only be 1
    metric_value = json.loads(spec["metrics"][0]["value"])

    # Get the current replicas from the metric
    current_replicas = metric_value["current_replicas"]

    # Get the average utilization from the metric
    average_utilization = metric_value["average_utilization"]

    # Get target and error margins
    target_average_utilization = metric_value["target_utilization"]
    kp = metric_value["kp"]
    ki = metric_value["ki"]
    kd = metric_value["kd"]
    max_integral = metric_value["max_integral"]

    # Load the last metric from file
    last_it_controller = read_last_it_from_file("last_it.txt", PIDController(kp, ki, kd, target_average_utilization))
    target_replicas = current_replicas
    evaluation = {}

    # Runs PID algorithm
    target_replicas = current_replicas - last_it_controller.update(average_utilization, time.time())

    # Build JSON dict with targetReplicas
    evaluation["targetReplicas"] = round(target_replicas)

    # Output JSON to stdout
    sys.stdout.write(json.dumps(evaluation))

    # Write last metric to file
    write_last_it_to_file("last_it.txt", last_it_controller)

if __name__ == "__main__":
    main()
