resource "aws_sqs_queue" "payment_events" {
  name = "payment-events"

  tags = {
    Name        = "payment-events"
    Environment = var.environment
  }
}