variable "memory_size" {
  type        = number
  description = "(optional) the amount of memory in MB. Defaults to 128."
  default     = 128
}

variable "timeout_seconds" {
  type        = number
  description = "(optional) the timeout in seconds for the function. Defaults to 15."
  default     = 15
}
