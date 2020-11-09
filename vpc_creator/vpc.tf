# AWS region for creating the VPC 
provider "aws" {
  region = var.region
}

# Creation of VPC 
resource "aws_vpc" "vpc_prod" {
  cidr_block = var.vpc_cidr

  tags = {
    Name = "vpc_prod"
  }
}


# Creating public subnets
resource "aws_subnet" "subnet_pub_prod" {
  count = "${length(var.avalable_zones)}"
  availability_zone = "${element(var.avalable_zones, count.index)}"
  vpc_id = "${aws_vpc.vpc_prod.id}"
  cidr_block = "${element(var.subnet_pub_cidr, count.index)}"
  depends_on = ["aws_internet_gateway.gateway_prod"]
  map_public_ip_on_launch = true
  tags = {
    Name = "subnet_pub_prod_${count.index}"
  }
}

# Creating internet gateway for the VPC 
resource "aws_internet_gateway" "gateway_prod" {
  vpc_id = "${aws_vpc.vpc_prod.id}"

  tags = {
    Name = "gateway_prod"
  }
}

# Creating route table for Internet Gateway
resource "aws_route_table" "route_table_pub_prod" {
  vpc_id = "${aws_vpc.vpc_prod.id}"
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_internet_gateway.gateway_prod.id}"
  }
  tags = {
    Name = "route_table_pub_prod"
  }
}

# Creating routes for public subnets
resource "aws_route_table_association" "route_pub_prod" {
  count          = "${length(var.avalable_zones)}"
  subnet_id      = "${element(aws_subnet.subnet_pub_prod.*.id, count.index)}"
  route_table_id = "${aws_route_table.route_table_pub_prod.id}"
}


# Creating private subnets 
resource "aws_subnet" "subnet_priv_prod" {
  count = "${length(var.avalable_zones)}"
  availability_zone = "${element(var.avalable_zones, count.index)}"
  vpc_id = "${aws_vpc.vpc_prod.id}"
  cidr_block = "${element(var.subnet_priv_cidr, count.index)}"
  tags = {
    Name = "subnet_priv_prod_${count.index}"
  }
}

# Creating Elastic IP for NAT gateway
resource "aws_eip" "nat_ip_prod" {
  tags = {
    Name = "nat_ip_prod"
  }
}

# Creating NAT gateway
resource "aws_nat_gateway" "nat_gateway_prod" {
  allocation_id = "${aws_eip.nat_ip_prod.id}"
  subnet_id     = "${aws_subnet.subnet_pub_prod.*.id[0]}"
  depends_on = ["aws_internet_gateway.gateway_prod"]
  tags = {
    Name = "nat_gateway_prod"
  }
}

# Creating route table for NAT gateway
resource "aws_route_table" "route_table_priv_prod" {
  vpc_id       = "${aws_vpc.vpc_prod.id}"
  route {
    cidr_block = "0.0.0.0/0"
    nat_gateway_id = "${aws_nat_gateway.nat_gateway_prod.id}"
  }
  tags = {
    Name= "route_table_priv_prod"
  }
}

# Creating routes for private subnets 
resource "aws_route_table_association" "route_priv_prod" {
  count          = "${length(var.avalable_zones)}"
  subnet_id      = "${element(aws_subnet.subnet_priv_prod.*.id, count.index)}"
  route_table_id = "${aws_route_table.route_table_priv_prod.id}"
}
