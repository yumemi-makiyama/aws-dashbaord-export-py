#!/usr/bin/env python

'''
AWSの access_keyと secret_key は $HOME/.aws/credentials の default プロファイルを参照します。
'''

import copy
import json
import os
import pprint
import re
from datetime import datetime, timezone, timedelta

import boto3

DASHBOARD_NAME = "dashboard-name-heare"

PP = pprint.PrettyPrinter(indent=4)
CLIENT = boto3.client('cloudwatch')

TZ_JST = timezone(timedelta(hours=+9), 'JST')
START_TIME = datetime(2019, 8, 23, 0, 0, 0, 0, TZ_JST)
END_TIME = datetime(2019, 8, 23, 23, 59, 59, 0, TZ_JST)

# ファイルパスには使わない文字
NORMALIZE_PATH_PATTERN = re.compile(r'[\\|/|:|?|.|"|<|>|\| |]')


def metrics_normalize(src):
    # https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/APIReference/CloudWatch-Dashboard-Body-Structure.html#CloudWatch-Dashboard-Properties-Metrics-Array-Format
    normalized = []
    prev_metrics = src[0]
    normalized.append(prev_metrics)

    for short_metrics in src[1:]:
        full_metrics = []

        for e in short_metrics:
            if (type(e) is str and e.startswith(".")):
                full_metrics.extend(list(e))
            else:
                full_metrics.append(e)

        # 稀に（？）ドットの数がひとつ多いことがあるので、無理やり調整する
        # EC2/ECS の CPU利用率で発生する
        if (0 < len(full_metrics) and len(full_metrics) % 2 == 0):
            full_metrics.pop(0)

        for i in range(len(full_metrics)):
            full_metrics[i] = full_metrics[i] if (full_metrics[i] != '.') else prev_metrics[i]

        normalized.append(full_metrics)
        prev_metrics = full_metrics

    return normalized


def load_widgets_from(dashboard_name):
    dashboard_response = CLIENT.get_dashboard(DashboardName=dashboard_name)
    body = dashboard_response["DashboardBody"]
    body_json = json.loads(body)

    # PP.pprint(body_json)

    widgets = []

    for w in body_json["widgets"]:
        title = w['properties']['title'] if ('title' in w['properties']) else 'unknown-title'

        if (title == 'unknown-title'):
            print('unknown title widget')
            PP.pprint(w)

        # print (title)
        # if ( w['properties']['title'] == 'SNS') :
        #     PP.pprint(w['properties']['metrics'])

        # print ("↓----------------------")
        metrics = metrics_normalize(w['properties']['metrics'])
        # PP.pprint( metrics )
        # print ("----------------------")
        widgets.append({'title': title, 'metrics': metrics})

    return widgets


def load_metric(metrics):
    copied_metrics = copy.deepcopy(metrics)

    # print('-------------------------------------')
    ns = copied_metrics.pop(0)
    metrics_name = copied_metrics.pop(0)
    statics_dic = copied_metrics.pop()
    statics = {
        'period': statics_dic['period'] if ('period' in statics_dic) else 300,  # default 5 min
        'statistics': statics_dic['stat'] if ('stat' in statics_dic) else 'Sum'
    }

    dims = []
    while copied_metrics:
        dims.append({
            'Name': copied_metrics.pop(0),
            'Value': copied_metrics.pop(0)
        })
    label = statics_dic['label'] if ('label' in statics_dic) else '_'.join(d['Value'] for d in dims)

    # PP.pprint(metrics)
    # PP.pprint(dims)

    response = CLIENT.get_metric_statistics(
        Namespace=ns,
        MetricName=metrics_name,
        Dimensions=dims,
        StartTime=START_TIME,
        EndTime=END_TIME,
        Period=statics['period'],
        Statistics=[statics['statistics']]
    )

    rows = []
    for dp in response['Datapoints']:
        row = dp;
        row['Timestamp'] = row['Timestamp'].astimezone(TZ_JST).isoformat()
        row['Namespace'] = ns
        row['MetricName'] = metrics_name
        row['Dimensions'] = dims
        row['request_period'] = statics['period']
        row['statistics'] = statics['statistics']
        row['label'] = label
        rows.append(row)

    rows.sort(key=lambda x: x['Timestamp'])
    return {'label': label, 'rows': rows}


def main():
    for widget in load_widgets_from(DASHBOARD_NAME):
        for metrics in widget['metrics']:
            # PP.pprint(metric)

            # PP.pprint(metric)
            metric_data = load_metric(metrics)
            # PP.pprint(metric_data)

            dir = 'out' + '/' + NORMALIZE_PATH_PATTERN.sub('_', widget['title'])
            json_file_name = dir + '/' + NORMALIZE_PATH_PATTERN.sub('_', metric_data['label']) + '.json'

            if not os.path.exists(dir):
                os.makedirs(dir)

            print('writing to ' + json_file_name)
            with open(json_file_name, mode='w') as f:
                for d in metric_data['rows']:
                    f.write(json.dumps(d) + '\n')


if __name__ == '__main__':
    main()
