provider "aws" {
  region = var.region
}

resource "aws_launch_template" "aws_launch_template" {

  # Name for launch template
  name = var.aws_launch_template_name

  block_device_mappings {
    device_name = "/dev/sda1"

    ebs {
      volume_size = var.volume_size
    }
  }
  
  # AMI ID
  image_id = var.image_id
  
  # shutdown behavior
  instance_initiated_shutdown_behavior = var.instance_initiated_shutdown_behavior
  
  # Instance type
  instance_type = var.instance_type

  # Acces Key to assosiate with the ec2 instances
  key_name = var.key_name

  monitoring {
    enabled = var.monitoring
  }
  
  # Network interface
  network_interfaces {
    associate_public_ip_address = true
    security_groups = var.vpc_security_group_ids
  }

  # The avaialabilty zone for adding the instances
  placement {
    availability_zone = var.availability_zone
  }
  
  
  # Tags for resources
  tag_specifications {
    resource_type = "instance"
    tags = {
      "${element(var.tag_key, 1)}" = "${element(var.tag_value, 1)}"
    }
  }
}