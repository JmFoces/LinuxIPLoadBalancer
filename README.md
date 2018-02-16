# LinuxIPLoadBalancer
First approach to a linux IPv4 load balancer based on Iptables.
  -- python load_balancer.py  `ifconfig -a |grep eth[1-3]|cut -d" " -f1`

The automated deployment with Nftables is comming soon. For now you can find:
  -- nftables-rpdb explained.pdf an explanation about how to integrate both RPDB and nftables to load balance through N vpn tunnels to the internet.
