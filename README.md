## 📖 Overview

This is a mono repository for my home infrastructure and Kubernetes cluster. I try to adhere to Infrastructure as Code (IaC) and GitOps practices using the tools like [Ansible](https://www.ansible.com/), [Terraform](https://www.terraform.io/), [Kubernetes](https://kubernetes.io/), [Flux](https://github.com/fluxcd/flux2), [Renovate](https://github.com/renovatebot/renovate) and [GitHub Actions](https://github.com/features/actions).

---

## ⛵ Kubernetes

There is a template over at [onedr0p/flux-cluster-template](https://github.com/onedr0p/flux-cluster-template) if you wanted to try and follow along with some of the practices I use here.

### Installation

My cluster is [k3s](https://k3s.io/) provisioned overtop bare-metal Fedora Server using the [Ansible](https://www.ansible.com/) galaxy role [ansible-role-k3s](https://github.com/PyratLabs/ansible-role-k3s). This is a semi hyper-converged cluster, workloads and block storage are sharing the same available resources on my nodes while I have a separate server for (NFS) file storage.

🔸 _[Click here](./ansible/) to see my Ansible playbooks and roles._

### Core Components

- [projectcalico/calico](https://github.com/projectcalico/calico): Internal Kubernetes networking plugin.
- [rook/rook](https://github.com/rook/rook): Distributed block storage for peristent storage.
- [mozilla/sops](https://toolkit.fluxcd.io/guides/mozilla-sops/): Manages secrets for Kubernetes, Ansible and Terraform.
- [kubernetes-sigs/external-dns](https://github.com/kubernetes-sigs/external-dns): Automatically manages DNS records from my cluster in a cloud DNS provider.
- [jetstack/cert-manager](https://cert-manager.io/docs/): Creates SSL certificates for services in my Kubernetes cluster.
- [kubernetes/ingress-nginx](https://github.com/kubernetes/ingress-nginx/): Ingress controller to expose HTTP traffic to pods over DNS.

### GitOps

[Flux](https://github.com/fluxcd/flux2) watches my [cluster](./cluster/) folder (see Directories below) and makes the changes to my cluster based on the YAML manifests.

[Renovate](https://github.com/renovatebot/renovate) watches my **entire** repository looking for dependency updates, when they are found a PR is automatically created. When some PRs are merged [Flux](https://github.com/fluxcd/flux2) applies the changes to my cluster.

### Directories

This Git repository contains the following directories (_kustomizatons_) under [cluster](./cluster/).

```sh
📁 cluster      # k8s cluster defined as code
├─📁 flux       # flux components which are loaded before everything
└─📁 apps       # workloads in a categorized directory structure
```

### Networking

| Name                                          | CIDR              |
|-----------------------------------------------|-------------------|
| Management VLAN                               | `192.168.1.0/24`  |
| Kubernetes Nodes VLAN                         | `192.168.42.0/24` |
| Kubernetes external services (Calico w/ BGP)  | `192.168.69.0/24` |
| Kubernetes pods                               | `10.42.0.0/16`    |
| Kubernetes services                           | `10.43.0.0/16`    |

- HAProxy configured on my `Opnsense` router for the Kubernetes Control Plane Load Balancer.
- Calico configured with `externalIPs` to expose Kubernetes services with their own IP over BGP (w/ECMP) which is configured on my router.

### Data Backup and Recovery

Rook does not have built in support for backing up PVC data so I am currently using a DIY _(or more specifically a "Poor Man's Backup")_ solution that is leveraging [Kyverno](https://kyverno.io/), [Kopia](https://kopia.io/) and native Kubernetes `CronJob` and `Job` resources.

At a high level the way this operates is that:

- Kyverno creates a `CronJob` for each `PersistentVolumeClaim` resource that contain a label of `snapshot.home.arpa/enabled: "true"`
- Everyday the `CronJob` creates a `Job` and uses Kopia to connect to a Kopia repository on my NAS over NFS and then snapshots the contents of the app data mount into the Kopia repository
- The snapshots made by Kopia are incremental which makes the `Job` run very quick.
- The app data mount is frozen during backup to prevent writes and unfrozen when the snapshot is complete.
- Recovery is a manual process. By using a different `Job` a temporary pod is created and the fresh PVC and existing NFS mount are attached to it. The data is then copied over to the fresh PVC and the temporary pod is deleted.

🔸 _[Velero](https://github.com/vmware-tanzu/velero), [Benji](https://github.com/elemental-lf/benji), [Gemini](https://github.com/FairwindsOps/gemini), [Kasten K10 by Veeam](https://www.kasten.io/product/), [Stash by AppsCode](https://stash.run/) are some alternatives but have limitations._

---

## 🌐 DNS

### Ingress Controller

Over WAN, I have port forwarded ports `80` and `443` to the load balancer IP of my ingress controller that's running in my Kubernetes cluster.

[Cloudflare](https://www.cloudflare.com/) works as a proxy to hide my homes WAN IP and also as a firewall. When not on my home network, all the traffic coming into my ingress controller on port `80` and `443` comes from Cloudflare. In `Opnsense` I block all IPs not originating from the [Cloudflares list of IP ranges](https://www.cloudflare.com/ips/).

🔸 _Cloudflare is also configured to GeoIP block all countries except a few I have whitelisted_

### Internal DNS

[coredns](https://github.com/coredns/coredns) is deployed on my `Opnsense` router and all DNS queries for my domains are forwarded to [k8s_gateway](https://github.com/ori-edge/k8s_gateway) that is running in my cluster. With this setup `k8s_gateway` has direct access to my clusters ingresses and services and serves DNS for them in my internal network.

### Ad Blocking

[AdGuard Home](https://github.com/AdguardTeam/AdGuardHome) is deployed on my `Opnsense` router which has a upstream server pointing the `coredns` instance I mentioned above. `Adguard Home` listens on my `MANAGEMENT`, `SERVER`, `IOT` and `GUEST` networks on port `53` meanwhile `coredns` only listens on `127.0.0.1:53`. In my firewall rules I have NAT port redirection forcing all the networks to use the `Adguard Home` DNS server.

### External DNS

[external-dns](https://github.com/kubernetes-sigs/external-dns) is deployed in my cluster and configure to sync DNS records to [Cloudflare](https://www.cloudflare.com/). The only ingresses `external-dns` looks at to gather DNS records to put in `Cloudflare` are ones that I explicitly set an annotation of `external-dns.home.arpa/enabled: "true"`

🔸 _[Click here](./terraform/cloudflare) to see how else I manage Cloudflare with Terraform._

### Dynamic DNS

My home IP can change at any given time and in order to keep my WAN IP address up to date on Cloudflare. I have deployed a [CronJob](./cluster/apps/networking/cloudflare-ddns) in my cluster, this periodically checks and updates the `A` record `ipv4.domain.tld`.

---

## 🔧 Hardware

<details>
  <summary>Click to see da rack!</summary>

  <img src="https://user-images.githubusercontent.com/213795/172947261-65a82dcd-3274-45bd-aabf-140d60a04aa9.png" align="center" width="200px" alt="rack"/>
</details>

| Device                    | Count | OS Disk Size | Data Disk Size              | Ram  | Operating System | Purpose             |
|---------------------------|-------|--------------|-----------------------------|------|------------------|---------------------|
| Protectli FW6D            | 1     | 500GB mSATA  | -                           | 16GB | Opnsense 22      | Router              |
| Intel NUC8i3BEK           | 3     | 256GB NVMe   | -                           | 32GB | Fedora 36        | Kubernetes Masters  |
| Intel NUC8i5BEH           | 3     | 240GB SSD    | 1TB NVMe (rook-ceph)        | 64GB | Fedora 36        | Kubernetes Workers  |
| PowerEdge T340            | 1     | 2TB SSD      | 8x12TB ZFS (mirrored vdevs) | 64GB | Ubuntu 22.04     | NFS + Backup Server |
| Lenovo SA120              | 1     | -            | 6x12TB (+2 hot spares)      | -    | -                | DAS                 |
| Raspberry Pi              | 1     | 32GB (SD)    | -                           | 4GB  | PiKVM            | Network KVM         |
| TESmart 8 Port KVM Switch | 1     | -            | -                           | -    | -                | Network KVM (PiKVM) |
| APC SMT1500RM2U w/ NIC    | 1     | -            | -                           | -    | -                | UPS                 |
| Unifi USP PDU Pro         | 1     | -            | -                           | -    | -                | PDU                 |

---

## 🤝 Gratitude and Thanks

Thanks to all the people who donate their time to the [Kubernetes @Home](https://github.com/k8s-at-home/) community. A lot of inspiration for my cluster comes from the people that have shared their clusters with the [k8s-at-home](https://github.com/topics/k8s-at-home) GitHub topic.

---

## 📜 Changelog

See [commit history](https://github.com/onedr0p/home-ops/commits/main)

---

## 🔏 License

See [LICENSE](./LICENSE)
