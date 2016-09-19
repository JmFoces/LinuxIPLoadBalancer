# LinuxIPLoadBalancer
First approach to a linux IPv4 load balancer.

python load_balancer.py  `ifconfig -a |grep eth[1-3]|cut -d" " -f1`
