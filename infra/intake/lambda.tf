resource "aws_lambda_function" "api" {
  function_name = "intake-api"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "main.handler"
  runtime       = "python3.12"

  filename         = "${path.module}/../../services/intake/lambda_package.zip"
  source_code_hash = filebase64sha256("${path.module}/../../services/intake/lambda_package.zip")

  timeout     = 15
  memory_size = 256

  vpc_config {
    subnet_ids         = data.aws_subnets.default.ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      DATABASE_URL = "postgresql://${aws_db_instance.intake.username}:${var.db_password}@${aws_db_instance.intake.address}:${aws_db_instance.intake.port}/${aws_db_instance.intake.db_name}"
    }
  }

  tags = {
    Name        = "intake-api"
    Environment = var.environment
  }
}

resource "aws_lambda_function" "relay" {
  function_name = "intake-relay"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "relay.lambda_handler"
  runtime       = "python3.12"

  filename         = "${path.module}/../../services/intake/lambda_package.zip"
  source_code_hash = filebase64sha256("${path.module}/../../services/intake/lambda_package.zip")

  timeout     = 30
  memory_size = 256

  vpc_config {
    subnet_ids         = data.aws_subnets.default.ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      DATABASE_URL              = "postgresql://${aws_db_instance.intake.username}:${var.db_password}@${aws_db_instance.intake.address}:${aws_db_instance.intake.port}/${aws_db_instance.intake.db_name}"
      SQS_ENDPOINT_URL          = "" # empty -- boto3 will use the real AWS SQS endpoint instead of LocalStack
      PAYMENT_EVENTS_QUEUE_NAME = aws_sqs_queue.payment_events.name
    }
  }

  tags = {
    Name        = "intake-relay"
    Environment = var.environment
  }
}

# Runs the relay Lambda automatically on a schedule, same idea as an
# EventBridge-scheduled poller in a real production setup
resource "aws_cloudwatch_event_rule" "relay_schedule" {
  name                = "intake-relay-schedule"
  description         = "Triggers the Intake outbox relay every minute"
  schedule_expression = "rate(1 minute)"
}

resource "aws_cloudwatch_event_target" "relay_target" {
  rule      = aws_cloudwatch_event_rule.relay_schedule.name
  arn       = aws_lambda_function.relay.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.relay.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.relay_schedule.arn
}

resource "aws_lambda_function" "migrate" {
  function_name = "intake-migrate"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "migrate.lambda_handler"
  runtime       = "python3.12"

  filename         = "${path.module}/../../services/intake/lambda_package.zip"
  source_code_hash = filebase64sha256("${path.module}/../../services/intake/lambda_package.zip")

  timeout     = 30
  memory_size = 256

  vpc_config {
    subnet_ids         = data.aws_subnets.default.ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      DATABASE_URL = "postgresql://${aws_db_instance.intake.username}:${var.db_password}@${aws_db_instance.intake.address}:${aws_db_instance.intake.port}/${aws_db_instance.intake.db_name}"
    }
  }

  tags = {
    Name        = "intake-migrate"
    Environment = var.environment
  }
}