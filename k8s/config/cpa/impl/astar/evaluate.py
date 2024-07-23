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

target_average_utilization = 70

def main():
    # Parse JSON into a dict
    spec = json.loads(sys.stdin.read())
    evaluate(spec)

def write_last_metric_to_file(file_path, new_content):
    with open(file_path, 'w') as file:
        file.write(str(new_content))

def read_last_metric_from_file(file_path, default_value=0.0):
    try:
        with open(file_path, 'r') as file:
            content = file.read().strip()
            if content == '':
                return default_value  # Return default value if file is empty
            
            # Convert the content to float
            float_value = float(content)
            
            return float_value
    except FileNotFoundError:
        return default_value
    except ValueError:
        return default_value
    except IOError:
        return default_value

def low_voltage_stage(average_utilization, last_average_utilization, current_replicas):
    if average_utilization > last_average_utilization:
        return current_replicas + 1
    else:
        return current_replicas / 2

def high_voltage_state(average_utilization, last_average_utilization, current_replicas):
    if average_utilization < last_average_utilization:
        return current_replicas - 1
    else:
        return current_replicas * 2

def optimum_voltage_state(current_replicas):
    return current_replicas

# hpa: desiredReplicas = ceil[currentReplicas * ( currentMetricValue / desiredMetricValue )]
# fonte: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/

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

    # Load the last metric from file
    last_metric = read_last_metric_from_file("last_metric.txt", average_utilization)
    target_replicas = current_replicas

    # Runs AsTAR algorithm
    if average_utilization > target_average_utilization:
        target_replicas = high_voltage_state(average_utilization, last_metric, current_replicas)
    elif average_utilization < target_average_utilization:
        target_replicas = low_voltage_stage(average_utilization, last_metric, current_replicas)
    else:
        target_replicas = optimum_voltage_state()

    # Build JSON dict with targetReplicas
    evaluation = {}
    evaluation["targetReplicas"] = math.ceil(target_replicas)

    # Output JSON to stdout
    sys.stdout.write(json.dumps(evaluation))

    # Write last metric to file
    write_last_metric_to_file("last_metric.txt", average_utilization)

if __name__ == "__main__":
    main()
