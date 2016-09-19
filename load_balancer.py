from utils import *
import os
import shutil
import sys
import time
RT_TABLES="/etc/iproute2/rt_tables"
load_balance_table_name="lb_ppp"


def reset_iptables():
	print "IPtables Reset "
	launch_interactive_command("iptables -P INPUT ACCEPT")
	launch_interactive_command("iptables -P OUTPUT ACCEPT")
	launch_interactive_command("iptables -P FORWARD DROP")
	launch_interactive_command("iptables -Z")
	launch_interactive_command("iptables -F")
	launch_interactive_command("iptables -t nat -F")
	launch_interactive_command("iptables -t mangle -F ")
	launch_interactive_command("iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu")
	launch_interactive_command("ebtables -I INPUT -i eth0 -j ACCEPT")
	launch_interactive_command("ebtables -I OUTPUT -o eth0 -j ACCEPT")
	launch_interactive_command("ebtables -P INPUT ACCEPT")
	launch_interactive_command("ebtables -P OUTPUT ACCEPT")
	launch_interactive_command("ebtables -P FORWARD DROP")
	launch_interactive_command("iptables -A INPUT -i eth0 -s 192.168.1.0/24 -j ACCEPT")
	launch_interactive_command("iptables -A OUTPUT -o eth0 -s 192.168.1.0/24 -j ACCEPT")
	launch_interactive_command("ebtables -I INPUT -i lo -j ACCEPT")
    launch_interactive_command("ebtables -I OUTPUT -o lo -j ACCEPT")	
	launch_interactive_command("iptables -P INPUT DROP ")
	launch_interactive_command("iptables -P OUTPUT DROP")
	launch_interactive_command("iptables -P FORWARD DROP")


def clear_routing_tables():
	routes = launch_command("ip route show table all |grep default|grep -v 'dev lo'")[1].split("\n")
	for route in routes:
		if route:
			launch_interactive_command("ip route del {0}".format(route))

def clear_ipsets():
	ip_sets = launch_command("ipset list|grep Name|cut -d' ' -f2")[1].split("\n")
	for ip_set in ip_sets:
		if ip_set:
			launch_command("ipset destroy {0}".format(ip_set))

def clear_ip_rules():
	rules = launch_command("ip rule|grep -v  \"^0\|^32766\|^32767\" |cut -d':' -f1")[1].split("\n")
	print "RULES: ", rules
	for rule_pref in rules:
		if rule_pref:
			launch_interactive_command("ip rule del pref {0}".format(rule_pref))


def set_rt_tables(wans):
	f = open(RT_TABLES,'w')
	f.write("#\r\n")
	f.write("# reserved values\r\n")
	f.write("#\r\n")
	f.write("255	local\r\n")
	f.write("254	main\r\n")
	f.write("253	default\r\n")
	f.write("0	unspec \r\n")
	f.write("# local \r\n")
	table_count=1
	for wan in wans:
		f.write("{0} {1}\n".format(table_count,wan))
		table_count+=1
	f.close()
	launch_interactive_command("cat {0}".format(RT_TABLES))

def add_default_load_balance_route(wans):
	f = open(RT_TABLES,'a')
	f.write("{0} {1}".format(100,load_balance_table_name))
	f.close()
	route_base = "ip route add default  proto static scope global table {0}".format(load_balance_table_name)
	for tmp_ifname in wans:
		launch_interactive_command("ip route add default dev {0} table {0}".format(tmp_ifname))
		route_base+=" nexthop  dev {0}  ".format(tmp_ifname)
	launch_interactive_command(route_base)
	launch_interactive_command("ip route del default")
	launch_interactive_command("ip route show table all")

def add_ipsets(wans):
	for tmp_ifname in wans:
		if tmp_ifname:
			launch_interactive_command("ipset create lb_{0} hash:ip,port,ip timeout 1200".format(tmp_ifname))
	launch_interactive_command("ipset list")

def set_iptables_and_fw_mark_rules(wans):
	launch_interactive_command(" iptables -t mangle -X SETMARK")
	launch_interactive_command(" iptables -t mangle -N SETMARK")
	launch_interactive_command(" iptables -t mangle -X GETMARK")
	launch_interactive_command(" iptables -t mangle -N GETMARK")
	launch_interactive_command(" iptables -t mangle -X CNTRACK")
	launch_interactive_command(" iptables -t mangle -N CNTRACK")

	launch_interactive_command("ip rule add prio 10 table main")

	mark_count=301
	prio_count=50
	for tmp_ifname in wans:
		if tmp_ifname:
			print "Ip rules for ", tmp_ifname
			launch_interactive_command(" ip rule add prio {2} fwmark 0x{1} table {0}".format(tmp_ifname,mark_count,prio_count))
			print ""
			mark_count+=1
			prio_count+=1
	launch_interactive_command("ip rule add prio 100 table {0}".format(load_balance_table_name))
	time.sleep(1)
	mark_count=301
	prio_count=50
	for tmp_ifname in wans:
		if tmp_ifname:
			print "SETMARK for ", tmp_ifname
			launch_interactive_command(" iptables -t mangle -A SETMARK -o {0} -j MARK --set-mark 0x{1}".format(tmp_ifname,mark_count))
			launch_interactive_command(" iptables -t mangle -A SETMARK -m mark --mark 0x{1} -m set ! --match-set lb_{0} src,dstport,dst -j SET --add-set lb_{0} src,dstport,dst".format(tmp_ifname,mark_count))
			print ""
			mark_count+=1
			prio_count+=1
	time.sleep(1)
	mark_count=301
	prio_count=50
	for tmp_ifname in wans:
		if tmp_ifname:
			print "GETMARK for ", tmp_ifname
			launch_interactive_command(" iptables -t mangle -A GETMARK -m mark --mark 0x0 -m set --match-set lb_{0} src,dstport,dst -j MARK --set-mark 0x{1}".format(tmp_ifname,mark_count))
			print ""
			mark_count+=1
			prio_count+=1
	mark_count=301
	prio_count=50
	time.sleep(1)
	for tmp_ifname in wans:
		if tmp_ifname:
			print "CNTRACK for ", tmp_ifname

			launch_interactive_command(" iptables -t mangle -A CNTRACK -o {0} -m mark --mark 0x0 -j SETMARK".format(tmp_ifname))
			print ""
			mark_count+=1
			prio_count+=1
	time.sleep(1)
	launch_interactive_command("iptables -t mangle -A CNTRACK -m mark ! --mark 0x0 -j CONNMARK --save-mark")
	for tmp_ifname in wans:
		if tmp_ifname:
			print "RATEST for ", tmp_ifname
			launch_interactive_command("iptables -t mangle -A POSTROUTING -o {0} -j RATEEST --rateest-name {0} --rateest-interval 250ms --rateest-ewma 0.5s".format(tmp_ifname))
			print ""
	launch_interactive_command("iptables -t mangle -A POSTROUTING -j CNTRACK")
	## A bit smart load balancer but... pending to improve this
	launch_interactive_command("iptables -t mangle -A PREROUTING -m conntrack --ctstate NEW -m rateest --rateest-delta --rateest1 <ifname0> --rateest-bps1 1kbit --rateest-gt --rateest2 <ifname1> --rateest-bps2 0kbit -j MARK --set-mark <MARK2>")
	launch_interactive_command("iptables -t mangle -A PREROUTING -m conntrack --ctstate NEW -m rateest --rateest-delta --rateest1 <ifname1> --rateest-bps1 1kbit --rateest-gt --rateest2 <ifname0> --rateest-bps2 0kbit -j MARK --set-mark <MARK1>")
	## EOF Improve ME!
	launch_interactive_command("iptables -t mangle -A PREROUTING -m mark --mark 0x0 -j CONNMARK --restore-mark")
	launch_interactive_command("iptables -t mangle -A PREROUTING -m mark --mark 0x0 -j GETMARK")

	launch_interactive_command("ifconfig -a |grep ppp |cut -d\" \" -f 1 | xargs -IX iptables -A OUTPUT -o X -j ACCEPT")
	launch_interactive_command("ifconfig -a |grep ppp |cut -d\" \" -f 1 | xargs -IX iptables -A INPUT -i X -m state --state RELATED,ESTABLISHED -j ACCEPT")
	
	launch_interactive_command("iptables -A FORWARD -i wlan0 -j ACCEPT")
	launch_interactive_command("iptables -A FORWARD -i eth0 -j ACCEPT")
	launch_interactive_command("iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT")
	launch_interactive_command("iptables -t nat -A POSTROUTING -j MASQUERADE")

	launch_interactive_command("ip rule show")


if __name__=="__main__":

	reset_iptables()
	clear_routing_tables()
	clear_ipsets()
	clear_ip_rules()


	try:
		wans=sys.argv[1].split() ##just ifconfig |grep <YourFilter> |cut -d" " -f1 and put input as second param
	except IndexError:
		print "Goodbye tell me wan interfaces. Example by lines ifconfig |grep <YourFilter> |cut -d" " -f1"

	set_rt_tables(wans)
	time.sleep(1)

	add_default_load_balance_route(wans)
	time.sleep(1)

	add_ipsets(wans)
	time.sleep(1)

	set_iptables_and_fw_mark_rules(wans)


