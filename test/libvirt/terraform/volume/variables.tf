variable "cluster_name" {
  type        = "string"
  description = "The name of the cluster."
}

variable "image" {
  description = "The URL of the OS disk image"
  type        = "string"
}
