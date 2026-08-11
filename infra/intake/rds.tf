resource "aws_db_instance" "intake" {
  identifier     = "intake-db"
  engine         = "postgres"
  engine_version = "16"
  instance_class = "db.t3.micro" # smallest instance size -- cheapest, plenty for a demo

  allocated_storage = 20
  storage_type       = "gp3"

  db_name  = "intake"
  username = "postgres"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.intake.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  publicly_accessible = false
  skip_final_snapshot = true # fine for a demo project; a real prod DB would keep a final snapshot on deletion

  tags = {
    Name        = "intake-db"
    Environment = var.environment
  }
}