# これは何

cloudwatch logsのログをS3に移行するlambda  
SAMの設定して`make bucket` 後に `make all` でデプロイされるはず  
バケット名が他と被って作れない場合はMakefileを修正  
DynamoDBテーブル(backup-cloudwatchlogs-to-s3-table)も同時に作成

# パラメーター

JSONで移行元のロググループ、移行先のバケット名を指定  
取得するログの日付も指定可（YYYY-MM-DD形式）

```
{
  "log_group_name": "XXXXX-log",
  "s3_bucket_name": "XXXXX-backup",
  "date": "2019-11-01"
}
```

日付はなくても実行可能、その場合は実行した日の前日のログを移行

```
{
  "log_group_name": "XXXXX-log",
  "s3_bucket_name": "XXXXX-backup"
}
```

log_group_nameを指定しない場合  
DynamoDBテーブルから取得した値で実行  
この場合は複数ロググループを一度に移行可能  
日付の指定はJSONのみで実行する場合と同様に指定可能

```
{
  "date": "2019-11-01"
}
```

DynamoDBテーブルに設定する値
```
id: 任意
log_group_name: ロググループ名
s3_bucket_name: S3バケット名
```

# 注意

JSONの`s3_bucket_name`で指定したバケットにはバケットポリシーの設定が必要  
【XXX】はバケット名に書き換える

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "logs.ap-northeast-1.amazonaws.com"
            },
            "Action": "s3:GetBucketAcl",
            "Resource": "arn:aws:s3:::【XXX】"
        },
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "logs.ap-northeast-1.amazonaws.com"
            },
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::【XXX】/*",
            "Condition": {
                "StringEquals": {
                    "s3:x-amz-acl": "bucket-owner-full-control"
                }
            }
        }
    ]
}
```
