# LinuxIPLoadBalancer
1. PoC with Iptables. Try: `python load_balancer.py  $(ifconfig -a |grep eth[1-3]|cut -d" " -f1)`

2. The automated deployment with Nftables is comming soon. For now just take a look at nftables-rpdb explained.pdf.
