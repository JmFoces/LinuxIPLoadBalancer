# LinuxIPLoadBalancer
1. PoC with Iptables. Try: `python load_balancer.py  $(ifconfig -a |grep eth[1-3]|cut -d" " -f1)`

2. I'm porting this to Nftables. For now just take a look at nftables-rpdb explained.pdf.
