resource "aws_apigatewayv2_api" "intake" {
  name          = "intake-api-gateway"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "intake_lambda" {
  api_id                 = aws_apigatewayv2_api.intake.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "intake_proxy" {
  api_id    = aws_apigatewayv2_api.intake.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.intake_lambda.id}"
}

resource "aws_apigatewayv2_stage" "intake" {
  api_id      = aws_apigatewayv2_api.intake.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "allow_apigateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.intake.execution_arn}/*/*"
}