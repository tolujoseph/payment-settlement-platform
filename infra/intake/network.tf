# Use the account's default VPC rather than building a custom one --
# simplest option for a demo project, no extra networking to manage.
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security group for RDS: only allow Postgres traffic (5432) from
# resources that explicitly reference this security group (i.e. our
# Lambda functions) -- nothing else, including the open internet, can
# reach the database.
resource "aws_security_group" "rds" {
  name        = "intake-rds-sg"
  description = "Allow Postgres access from Intake Lambda functions only"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "Postgres from Lambda"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "intake-rds-sg"
    Environment = var.environment
  }
}

# Security group for Lambda: needs outbound access to reach RDS and
# the internet (for SQS, since Lambda-in-VPC loses default internet
# access unless explicitly allowed out).
resource "aws_security_group" "lambda" {
  name        = "intake-lambda-sg"
  description = "Security group for Intake Lambda functions"
  vpc_id      = data.aws_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "intake-lambda-sg"
    Environment = var.environment
  }
}

resource "aws_db_subnet_group" "intake" {
  name       = "intake-db-subnet-group"
  subnet_ids = data.aws_subnets.default.ids

  tags = {
    Name        = "intake-db-subnet-group"
    Environment = var.environment
  }
}