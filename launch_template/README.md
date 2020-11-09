# AWS Launch template

## Files
**launch-tempate**
**variables**

## variables
#### Region
```terraform
variable "region" {
  default = "ap-south-1"
}
```
#### Launch tempalte name
```terraform
variable "aws_launch_template_name" {
  default = "template_one"
}
```
#### Volume size
```terraform
variable "volume_size" {
  default = 20
}
```
#### AMI ID
```terraform
variable "image_id" {
  default = "ami-06832d84cd1dbb448"
}
```
#### shutdown behavior - "terminate" or "stop"
```terraform
variable "instance_initiated_shutdown_behavior" {
  default = "stop"
}
```
#### Instance type
```terraform
variable "instance_type" {
  default = "t2.micro"
}
```
#### Access key to assosicate with the ec2 instances
```terraform
variable "key_name" {
  default = "chiju"
}
```
#### Monitoring
```terraform
variable "monitoring" {
  default = true
}
```
#### Avaialability zone for creating the instances
```terraform
variable "availability_zone" {
  default = "ap-south-1a"
}
```
#### Security group names
```terraform
variable "vpc_security_group_ids" {
  default = ["sg-072017b5ad89dc955"]
}
```
#### Instance tag keys
```terraform
variable "tag_key" {
  default = ["Name"]
}
```
#### Instance tag values
```terraform
variable "tag_value" {
  default = ["one"]
}
```

## launch-template

### Region
```terraform
provider "aws" {
  region = var.region
}
```
### AWS Launch template
```terraform
resource "aws_launch_template" "aws_launch_template" {
```

#### Name for launch template
 ```terraform
  name = var.aws_launch_template_name

  block_device_mappings {
    device_name = "/dev/sda1"

    ebs {
      volume_size = var.volume_size
    }
  }
 ```
 #### AMI ID
 ```terraform
  image_id = var.image_id
  ```
  
  #### shutdown behavior
  ```terraform
  instance_initiated_shutdown_behavior = var.instance_initiated_shutdown_behavior
```
 #### Instance type
```terraform
  instance_type = var.instance_type
```
  #### Acces Key to assosiate with the ec2 instances
 ```terraform
  key_name = var.key_name

  monitoring {
    enabled = var.monitoring
  }
  ```
  #### Network interface
  ```terraform
  network_interfaces {
    associate_public_ip_address = true
    security_groups = var.vpc_security_group_ids
  }
```

  #### The avaialabilty zone for adding the instances
  ```terraform
  placement {
    availability_zone = var.availability_zone
  }
  ```
  
  #### Tags for resources
  
  ```terraform
  tag_specifications {
    resource_type = "instance"
    tags = {
      "${element(var.tag_key, 1)}" = "${element(var.tag_value, 1)}"
    }
  }
}
```