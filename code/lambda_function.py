import datetime
import time
import boto3

log_group_name = 'log_group_name'
s3_bucket_name = 's3_bucket_name'


def lambda_handler(event, context):

    target_date = None
    if ('date' in event):
        # 日付を取得(YYYY-MM-DD形式)
        input_date = event['date']
        input_date_array = input_date.split('-')
        year = int(input_date_array[0])
        month = int(input_date_array[1])
        day = int(input_date_array[2])
        target_date = datetime.date(year, month, day)
    else:
        # 日付指定がなければ前日分を取得
        target_date = datetime.datetime.combine(
            datetime.date.today() - datetime.timedelta(days=1), datetime.time(0, 0, 0))

    if log_group_name in event:
        # パラメーターにロググループ指定があればそこだけ取得
        backup_from_json(event, target_date)
    else:
        # ロググループ指定がなければ複数ロググループを処理
        backup_from_dynamo(target_date)

    return 'END'


def backup_from_json(event, target_date):
    log_group = event[log_group_name]
    s3_bucket = event[s3_bucket_name]
    create_export_task(log_group, s3_bucket, target_date)


def backup_from_dynamo(target_date):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('backup-cloudwatchlogs-to-s3-table')
    response = table.scan()
    items = response['Items']

    for item in items:
        log_group = item[log_group_name]
        s3_bucket = item[s3_bucket_name]
        create_export_task(log_group, s3_bucket, target_date)


def create_export_task(log_group, s3_bucket, target_date):
    print('from LOG_GROUP:%s to S3_BUCKET:%s' %
          (log_group, s3_bucket))

    s3_prefix = '%s_exported_at_%s' % (target_date.strftime(
        "%Y-%m-%d"), (datetime.datetime.now()).strftime("%Y-%m-%d_%H:%M:%S"))
    from_ts = int(time.mktime(target_date.timetuple()))
    to_ts = int(from_ts + (60 * 60 * 24) - 1)

    print('Timestamp: from_ts %s, to_ts %s' % (from_ts, to_ts))

    # export開始
    client = boto3.client('logs')
    response = client.create_export_task(
        logGroupName=log_group,
        fromTime=from_ts * 1000,
        to=to_ts * 1000,
        destination=s3_bucket,
        destinationPrefix=s3_prefix
    )

    # 同時実行できないので完了まで待つ
    while True:
        res = client.describe_export_tasks(taskId=response['taskId'])
        status = res['exportTasks'][0]['status']['code']
        print(status)
        if status != 'RUNNING' and status != 'PENDING':
            break
        time.sleep(1)
