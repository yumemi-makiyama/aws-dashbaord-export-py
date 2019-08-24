AWS CloudWatch の ダッシュボードデータをエクスポート
===

AWS CloudWatchのダッシュボードに登録しているメトリクスをJSONファイルに書き出します。

## Description

CloudWatchで管理されているメトリクスは、保持期間が長い程に解像度が下がっていきます。
[メトリクスの保持](https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html) には
下の記載があります。

CloudWatch には、メトリクスデータが次のように保持されます。

* 期間が 60 秒未満のデータポイントは、3 時間使用できます。これらのデータポイントは高解像度カスタムメトリクスです。
* 期間が 60 秒 (1 分) のデータポイントは、15 日間使用できます。
* 期間が 300 秒 (5 分) のデータポイントは、63 日間使用できます。
* 期間が 3600 秒 (1 時間) のデータポイントは、455 日 (15 か月) 間使用できます。

最初は短い期間で発行されるデータポイントは、長期的なストレージのため一緒に集計されます。
たとえば、1 分の期間でデータを収集する場合、データは 1 分の解像度で 15 日にわたり利用可能になります。
15 日を過ぎてもこのデータはまだ利用できますが、集計され、5 分の解像度のみで取得可能になります。
63 日を過ぎるとこのデータはさらに集計され、1 時間の解像度のみで利用できます。

CloudWatch は、2016 年 7 月 9 日の時点で 5 分および 1 時間のメトリクスデータを保持し始めました。

引用ここまで。

そのため、後日に高解像度のデータを参照することができません。特にデータソースがCloudWatchだけにある場合は
必要なデータが欠損する状態になります。

システム運用する上で不便なので、ダッシュボードに登録されたメトリクスをJSONファイルに書き出し、
高解像度のメトリクスを別のデータストレージで長期間保存を可能にします。

## Demo

### 出力されるファイルのディレクトリ構成

```
out
  +- [ウィジェット名]
  |   +- [ダッシュボードでのラベル].json
  +- EC2-ASG
      +- ASG_front-api.json
      +- ASG_microservice1.json
      +- EC2_batch-server-1.json
      +- EC2_batch-server-2.json
```

### JSONファイルの内容

下の様なファイルを書き出します。

```

{"Timestamp": "2019-08-23T08:30:00+09:00", "Maximum": 1.25, "Unit": "Percent", "Namespace": "AWS/EC2", "MetricName": "CPUUtilization", "Dimensions": [{"Name": "InstanceId", "Value": "i-0665991afecf1daf1"}], "request_period": 60, "statistics": "Maximum", "label": "EC2 batch-server-2"}
{"Timestamp": "2019-08-23T08:35:00+09:00", "Maximum": 1.44067796606223, "Unit": "Percent", "Namespace": "AWS/EC2", "MetricName": "CPUUtilization", "Dimensions": [{"Name": "InstanceId", "Value": "i-0123456789abcdefg"}], "request_period": 60, "statistics": "Maximum", "label": "EC2 batch-server-2"}
{"Timestamp": "2019-08-23T08:40:00+09:00", "Maximum": 1.33333333321692, "Unit": "Percent", "Namespace": "AWS/EC2", "MetricName": "CPUUtilization", "Dimensions": [{"Name": "InstanceId", "Value": "i-0123456789abcdefg"}], "request_period": 60, "statistics": "Maximum", "label": "EC2 batch-server-2"}
{"Timestamp": "2019-08-23T08:45:00+09:00", "Maximum": 63.3606557377431, "Unit": "Percent", "Namespace": "AWS/EC2", "MetricName": "CPUUtilization", "Dimensions": [{"Name": "InstanceId", "Value": "i-0123456789abcdefg"}], "request_period": 60, "statistics": "Maximum", "label": "EC2 batch-server-2"}
{"Timestamp": "2019-08-23T08:50:00+09:00", "Maximum": 59.1525423729208, "Unit": "Percent", "Namespace": "AWS/EC2", "MetricName": "CPUUtilization", "Dimensions": [{"Name": "InstanceId", "Value": "i-00123456789abcdefg}], "request_period": 60, "statistics": "Maximum", "label": "EC2 batch-server-2"}
{"Timestamp": "2019-08-23T08:55:00+09:00", "Maximum": 12.4576271186046, "Unit": "Percent", "Namespace": "AWS/EC2", "MetricName": "CPUUtilization", "Dimensions": [{"Name": "InstanceId", "Value": "i-0123456789abcdefg"}], "request_period": 60, "statistics": "Maximum", "label": "EC2 batch-server-2"}
{"Timestamp": "2019-08-23T09:00:00+09:00", "Maximum": 12.213114754022, "Unit": "Percent", "Namespace": "AWS/EC2", "MetricName": "CPUUtilization", "Dimensions": [{"Name": "InstanceId", "Value": "i-0123456789abcdefg"}], "request_period": 60, "statistics": "Maximum", "label": "EC2 batch-server-2"}
{"Timestamp": "2019-08-23T09:05:00+09:00", "Maximum": 1.25, "Unit": "Percent", "Namespace": "AWS/EC2", "MetricName": "CPUUtilization", "Dimensions": [{"Name": "InstanceId", "Value": "i-0123456789abcdefg"}], "request_period": 60, "statistics": "Maximum", "label": "EC2 batch-server-2"}
{"Timestamp": "2019-08-23T09:10:00+09:00", "Maximum": 1.06557377052997, "Unit": "Percent", "Namespace": "AWS/EC2", "MetricName": "CPUUtilization", "Dimensions": [{"Name": "InstanceId", "Value": "i-0123456789abcdefg"}], "request_period": 60, "statistics": "Maximum", "label": "EC2 batch-server-2"}
{"Timestamp": "2019-08-23T09:15:00+09:00", "Maximum": 1.27118644067797, "Unit": "Percent", "Namespace": "AWS/EC2", "MetricName": "CPUUtilization", "Dimensions": [{"Name": "InstanceId", "Value": "i-0123456789abcdefg"}], "request_period": 60, "statistics": "Maximum", "label": "EC2 batch-server-2"}

```

JSONの要素は下の通りです。

* Timestamp : ISO形式のタイムスタンプ。
* Maximum: 統計値。統計方法に応じてラベルが変化する。
* Unit: 統計値の単位。
* Namespace: CloudWatch メトリクスの名前空間。
* MetricName: CloudWatch メトリクス名。
* Dimensions: CloudWatch メトリクスのディメンジョン。
* request_period: メトリクスを取得するリクエストに指定した、統計の期間。
* statistics: 集計方法。
* label: ダッシュボードでのラベ


統計値と単位については https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html#Statisticc を参照してください。

## Requirement

* Python 3.7
* boto3 1.9.214

## Usage

### AWSの認証情報

boto3 を利用してAWSリソースにアクセスするために、適切な認証情報が必要です。

最も簡単な方法は `~/.aws/credentials` の `default` プロファイルに認証情報を設定しておくことです。
 
詳しくは https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html を
参照してください。


## Install

pipenv で依存するライブラリをインストールしてください。

```
$ pipenv sync
```


## Licence

[MIT](https://github.com/tcnksm/tool/blob/master/LICENCE)

## Author

[m_akiyama](https://github.com/yumemi-makiyama)

