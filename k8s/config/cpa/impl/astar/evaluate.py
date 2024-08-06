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

def main():
    # Parse JSON into a dict
    spec = json.loads(sys.stdin.read())
    evaluate(spec)

def exponential_moving_average(current_value: float, previous_ema: float, alpha=0.3):
    return alpha * current_value + (1 - alpha) * previous_ema

def write_last_metric_to_file(file_path: str, new_content):
    with open(file_path, 'w') as file:
        file.write(str(new_content))

def read_last_metric_from_file(file_path: str, default_value=0.0):
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

def low_resource_usage(average_resource_utilization: float, last_average_resource_utilization: float, current_replicas: int, error_margin: float):
    if average_resource_utilization > last_average_resource_utilization + error_margin:
        return current_replicas + 1
    else:
        return current_replicas / 2

def high_resource_usage(average_resource_utilization: float, last_average_resource_utilization: float, current_replicas: int, error_margin: float):
    if average_resource_utilization < last_average_resource_utilization - error_margin:
        return current_replicas - 1
    else:
        return current_replicas * 2

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
    error_margin = metric_value["error_margin"]

    # Load the last metric from file
    last_metric = read_last_metric_from_file("last_metric.txt", average_utilization)
    target_replicas = current_replicas
    evaluation = {}

    # Runs AsTAR algorithm
    if average_utilization >= target_average_utilization:
        target_replicas = high_resource_usage(average_utilization, last_metric, current_replicas, error_margin)
        evaluation["usageMode"] = "high_resource_usage"
    else:
        target_replicas = low_resource_usage(average_utilization, last_metric, current_replicas, error_margin)
        evaluation["usageMode"] = "low_resource_usage"

    # Build JSON dict with targetReplicas
    evaluation["targetReplicas"] = math.ceil(target_replicas)

    # Output JSON to stdout
    sys.stdout.write(json.dumps(evaluation))

    # Write last metric to file
    write_last_metric_to_file("last_metric.txt", exponential_moving_average(average_utilization, last_metric))

if __name__ == "__main__":
    main()
