resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  actions_enabled                       = true
  alarm_actions                         = ["arn:aws:sns:us-east-1:402889198055:us-east-1-alarms"]
  alarm_description                     = "# lambda errors us-east-1"
  alarm_name                            = "lambda_erros"
  comparison_operator                   = "GreaterThanOrEqualToThreshold"
  datapoints_to_alarm                   = 3
  dimensions                            = {}
  evaluate_low_sample_count_percentiles = null
  evaluation_periods                    = 1
  extended_statistic                    = null
  insufficient_data_actions             = []
  metric_name                           = "Errors"
  namespace                             = "AWS/Lambda"
  ok_actions                            = []
  period                                = 86400
  statistic                             = "Sum"
  threshold                             = 1
  threshold_metric_id                   = null
  treat_missing_data                    = "missing"
  unit                                  = null
}

import {
  to = aws_cloudwatch_metric_alarm.lambda_errors
  id = "Lambda Errors"
}