variable "kube_server_count" {
  default = 0
}
variable "kube_agent_count" {
  default = 0
}
variable "kube_server_disksize" {
  default = "10G"
}
variable "kube_agent_disksize" {
  default = "20G"
}

variable "k3_server_count" { default = 1 }
variable "k3_agent_count" { default = 1 }
variable "k3_server_disksize" { default = "30G" }
variable "k3_server_base_offset" { default = 50 } # IP base offset, start counting from x.x.x.50
variable "k3_agent_disksize" { default = "80G" }
variable "k3_agent_base_offset" { default = 60 } # IP base offset, start counting from x.x.x.60
variable "k3_dev_offset" { default = 70 } # IP base offset, start counting from x.x.x.70

variable "k3_server00_offset" { default = 0 }
variable "k3_server00_host" { default = "yurika" }

variable "k3_server01_offset" { default = 1 }
variable "k3_server01_host" { default = "yurika" }

variable "k3_server02_offset" { default = 2 }
variable "k3_server02_host" { default = "melfina" }

variable "k3_agent00_offset" { default =0 }
variable "k3_agent00_mem" { default = "26624" }
variable "k3_agent00_disksize" { default = "400G" }
variable "k3_agent00_host" { default = "eclair" }

variable "k3_agent01_offset" { default = 1 }
variable "k3_agent01_mem" { default = "26624" }
variable "k3_agent01_disksize" { default = "200G" }
variable "k3_agent01_host" { default = "nono" }

variable "k3_agent02_offset" { default = 2 }
variable "k3_agent02_mem" { default = "26624" }
variable "k3_agent02_disksize" { default = "400G" }
variable "k3_agent02_host" { default = "ifurita" }

variable "k3_dev_server00_offset" { default = 0 }
variable "k3_dev_server00_mem" { default = "12120" }
variable "k3_dev_server00_cores" { default = "4" }
variable "k3_dev_server00_disksize" { default = "200G" }
variable "k3_dev_server00_host" { default = "melfina" }

variable "k3_dev_agent00_offset" { default = 1 }
variable "k3_dev_agent00_mem" { default = "24480" }
variable "k3_dev_agent00_cores" { default = "4" }
variable "k3_dev_agent00_disksize" { default = "200G" }
variable "k3_dev_agent00_host" { default = "lafiel" }

variable "ssh_key_worklaptop" {
  default = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+ZxDKfNmtdDEbYUNl4pQfYlatwD75uhcNkl5S/b/IdOT4Km/x1mpmkkaOonSUoPgucjgWHWebgNDYeJ3yoWjSMu4jzi5zBByXH9n2GsH50rQ/E7qwTogEfivIrzhxkHPCLy85Uy1Z7/FhZoe+B9YGmt9NHrI2Wy4FJd2pyfXg7YqeG2uaHy4ix2VAHS0kqbWfCnT13L1RO592CN3aINUAC8s54/DrLw1NKDBkN8S/c/FXNRwRQ84Auy4M5l+MXAMQl2EXab4rdaiwWN+Is00BANcckFZraQX9GgQYTWLlFTN+9CSEbQohRABYBpmeSizgDYM5e2SbVObbXBzWaztB mikekao@SEA-1800428659H"
}
variable "ssh_key_terraform" {
  default = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCVnuGiYRF0KdNfaBmrUgU2gaS7zC2e7tWgOg65wSod7lfCNuKV8j7Hdg53mF2cc6WIiOV14oWNNpo5wqFNJf4hP9ytecASTsoLEheCIFY+6bTfQHAirF5LoaHHplF0xa11V0SWzehcSB+bFsS9KiRlIY99YXyZ+uoSiJ5eLkUfBMxoS1zu2p3a/M+eaFxropdDY3yXZ2C3p0UpaRyM4Kpom4mHSUQz07Ii5PaT11B7FExb+xMKATf30n85sziH3kbBbWQ5emD9SAhHeetOO5QLJPNJwbYYW7R8j25R1v9mDQSrYQ96u2vwTIq6dUaC3rxHHtFm6CwVQ71MLqUrP9eG5F07+UH29tOlCVqwkBfnKyME+J4ZInQXc2qxWt6gGZigCMF4Kcl3GDxxLvJZlh+AiQpwjnacX6v5xY8HL31JgiMQf2x8nUakmAJ2+LWpdhYFmp8c+HWNXp6b9MIs02TNkDC2sK2h9lyDEz+8oKfwTAYGMWZQYFS51egVlloIEpE= ubuntu@terraform"
}
variable "ssh_key_hitagi" {
  default = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDOJphAZm067472n+Cu8y0rK3m/fiNPYw8PXfcDnOaED396Lq7jvZeqUX9szL2+e/hM0K5GQ6BQLulsFC75qbBZfUbYpKnhjmPHQSy4Be98LhVsHBv7Xxie2MoReKyWyx4wQdUqBaWvzaPZJMvFagyuNVK1erlKX+EnoPYXXEtOEAPKnz2V5rj9du8YQVVj+/wANTg4A6+L8lAC3Pp//8xRAbq+TUTVd27YUcQ8W958OQpykGSQKpp6gW1+MMzhQF+dSzNHzlWWWNZMyslRsBDpR7+r+idpjcbK0hthSxE2wf1Dt7VWzqaCJij2z74ofhzoEL5t4MLu/Cfj0vKr87cvVfWpktYXjycsMivIbYKdR3IKuMvYt+W02C7fSg4j368QnCaVrPbOMxIj5xAcTVo/hy6p9NsbBleGBb1HIB8wdBtHPnDq39Ps3olPmDr5wWvAF1o07RI/pogXX2TL67rpBzKtuiRm62QYf691CbOh8cnsr3aYtlK3Q1bEZFIsB5E= lenaxia@Hitagi"
}

variable "proxmox_hosts" {
    default = [ "lafiel", "melfina", "yurika", "nono", "eclair", "ifurita" ]
}
variable "template_name" {
    default = "ubuntu-2004-cloudinit-template"
}
