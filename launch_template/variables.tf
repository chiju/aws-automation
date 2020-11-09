variable "region" {
  default = "ap-south-1"
}

# Launch tempalte name
variable "aws_launch_template_name" {
  default = "template_one"
}

# Volume size
variable "volume_size" {
  default = 20
}

# AMI ID
variable "image_id" {
  default = "ami-06832d84cd1dbb448"
}

# shutdown behavior - "terminate" or "stop"
variable "instance_initiated_shutdown_behavior" {
  default = "stop"
}

# Instance type
variable "instance_type" {
  default = "t2.micro"
}

# Access key to assosicate with the ec2 instances
variable "key_name" {
  default = "chiju"
}

# Monitoring
variable "monitoring" {
  default = true
}

# Avaialability zone for creating the instances
variable "availability_zone" {
  default = "ap-south-1a"
}

# Security group names
variable "vpc_security_group_ids" {
  default = ["sg-072017b5ad89dc955"]
}

# Instance tag keys
variable "tag_key" {
  default = ["Name"]
}

# Instance tag values
variable "tag_value" {
  default = ["one"]
}


