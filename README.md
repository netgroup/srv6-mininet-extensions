# SRv6 Mininet extensions  #

This projects is for creating mininet networks to emulate SRv6 

### Run an example experiment ###

    > cd /home/user/workspace/srv6-mantoo
    > git pull
    > cd mininet
    > ./start.sh

now you have started the topology defined in the file abilene.py (11 routers and 11 servers):

    # Define the routers representing the cities
    routers = ['nyc', 'chi', 'wdc', 'sea', 'sun', 'lan', 'den', 'kan', 'hou', 'atl', 'ind']

    # Define the servers representing the cities
    hosts = ['hnyc', 'hchi', 'hwdc', 'hsea', 'hsun', 'hlan', 'hden', 'hkan', 'hhou', 'hatl', 'hind']

The file topology.json in the deployment folder provides the topology with IPv6 addresses: 

    > cat /home/user/workspace/srv6-mantoo/deployment/topology.json

for example:

    "id": "chi", "mgmtip": "2000::2/64"
    "id": "den", "mgmtip": "2000::7/64"
    "id": "hden", "mgmtip": "2000::12/64", 

    "chi-eth2" : "2001:0:0:12::2/64"
    "den-eth1" : "2001:0:0:d::1/64"
    "hden-eth1" : "2001:0:0:d::2/64"

Each router and server has a management interface eth0 connected "out of band" with the host running mininet. 
You can login on any router or server using their management IP, for example login in the chi router and ping/traceroute the den router or the den host :

    # Connect to the node hync
    > ssh root@2000::c

    # Ping denver router 2001:0:0:d::1
    > ping -6 2001:0:0:d::1
    > PING 2001:0:0:d::1 56 data bytes
    > 64 bytes from 2001:0:0:d::1: icmp_seq=1 ttl=60 time=10.7 ms
    > 64 bytes from 2001:0:0:d::1: icmp_seq=2 ttl=60 time=0.167 ms
    > 64 bytes from 2001:0:0:d::1: icmp_seq=3 ttl=60 time=0.166 ms

    # Traceroute denver router 2001:0:0:d::1 
    > traceroute -6 2001:0:0:d::1
    > traceroute to 2001:0:0:d::1 (2001:0:0:d::1), 30 hops max, 80 byte packets
    > 1  2001:0:0:7::1 (2001:0:0:7::1)  0.061 ms  0.017 ms  0.014 ms
    > 2  2001:0:0:12::2 (2001:0:0:12::2)  0.033 ms  0.021 ms  0.018 ms
    > 3  2001:0:0:14::2 (2001:0:0:14::2)  2.744 ms  0.042 ms  0.017 ms
    > 4  2001:0:0:1d::1 (2001:0:0:1d::1)  1.151 ms  0.058 ms  0.025 ms
    > 5  2001:0:0:d::1 (2001:0:0:d::1)  0.038 ms  0.039 ms  0.084 ms

    # Ping denver host 2001:0:0:d::2
    > ping -6 2001:0:0:d::2
    > PING 2001:0:0:d::2(2001:0:0:d::2) 56 data bytes
    > 64 bytes from 2001:0:0:d::2: icmp_seq=1 ttl=59 time=4.88 ms
    > 64 bytes from 2001:0:0:d::2: icmp_seq=2 ttl=59 time=0.170 ms
    > 64 bytes from 2001:0:0:d::2: icmp_seq=3 ttl=59 time=0.166 ms

    # Traceroute denver host 2001:0:0:d::2
    > traceroute -6 2001:0:0:d::2
    > traceroute to 2001:0:0:d::2 (2001:0:0:d::2), 30 hops max, 80 byte packets
    > 1  2001:0:0:7::1 (2001:0:0:7::1)  0.059 ms  0.015 ms  0.012 ms
    > 2  2001:0:0:12::2 (2001:0:0:12::2)  0.032 ms  0.017 ms  0.016 ms
    > 3  2001:0:0:14::2 (2001:0:0:14::2)  0.033 ms  0.019 ms  0.018 ms
    > 4  2001:0:0:1d::1 (2001:0:0:1d::1)  0.094 ms  0.030 ms  0.023 ms
    > 5  2001:0:0:1b::1 (2001:0:0:1b::1)  0.050 ms  0.028 ms  0.027 ms
    > 6  2001:0:0:d::2 (2001:0:0:d::2)  0.043 ms  0.240 ms  0.048 ms
    
Now you can add SRv6 policies :

    # Connect to the nyc host
    > ssh root@2000::c

    # Traffic towards 2001:0:0:d::1 is steered through 2001::1
    > ip -6 r a 2001:0:0:d::1/128 encap seg6 mode encap segs 2001::1 dev hnyc-eth0

    # Ping denver router 2001:0:0:d::1
    > ping -6 2001:0:0:d::1
    > PING 2001:0:0:d::1(2001:0:0:d::1) 56 data bytes
    > 64 bytes from 2001:0:0:d::1: icmp_seq=1 ttl=60 time=0.193 ms
    > 64 bytes from 2001:0:0:d::1: icmp_seq=2 ttl=60 time=0.332 ms
    > 64 bytes from 2001:0:0:d::1: icmp_seq=3 ttl=60 time=0.222 ms

    # Traceroute denver router 2001:0:0:d::1 
    > traceroute -6 2001:0:0:d::1
    > traceroute to 2001:0:0:d::1 (2001:0:0:d::1), 30 hops max, 80 byte packets
    > 1  * * *
    > 2  * * *
    > 3  2001:0:0:14::2 (2001:0:0:14::2)  3.418 ms  0.086 ms  0.040 ms
    > 4  2001:0:0:1d::1 (2001:0:0:1d::1)  0.070 ms  0.045 ms  0.046 ms
    > 5  2001:0:0:d::1 (2001:0:0:d::1)  0.056 ms  0.043 ms  0.043 ms

    # Dump the traffic
    > tcpdump -nei hnyc-eth1
    > tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    > listening on hnyc-eth1, link-type EN10MB (Ethernet), capture size 262144 bytes
    > 12:35:16.325624 be:6d:ef:83:18:1a > 6e:53:c7:8d:05:df, ethertype IPv6 (0x86dd), length 182: 2001:0:0:7::2 > 2001::1: srcrt (len=2, type=4, segleft=0[|srcrt]
    > 12:35:16.325774 6e:53:c7:8d:05:df > be:6d:ef:83:18:1a, ethertype IPv6 (0x86dd), length 118: 2001:0:0:d::1 > 2001:0:0:7::2: ICMP6, echo reply, seq 1, length 64
    > 12:35:17.349270 be:6d:ef:83:18:1a > 6e:53:c7:8d:05:df, ethertype IPv6 (0x86dd), length 182: 2001:0:0:7::2 > 2001::1: srcrt (len=2, type=4, segleft=0[|srcrt]
    > 12:35:17.349476 6e:53:c7:8d:05:df > be:6d:ef:83:18:1a, ethertype IPv6 (0x86dd), length 118: 2001:0:0:d::1 > 2001:0:0:7::2: ICMP6, echo reply, seq 2, length 64
    > 12:35:18.373377 be:6d:ef:83:18:1a > 6e:53:c7:8d:05:df, ethertype IPv6 (0x86dd), length 182: 2001:0:0:7::2 > 2001::1: srcrt (len=2, type=4, segleft=0[|srcrt]
    > 12:35:18.373504 6e:53:c7:8d:05:df > be:6d:ef:83:18:1a, ethertype IPv6 (0x86dd), length 118: 2001:0:0:d::1 > 2001:0:0:7::2: ICMP6, echo reply, seq 3, length 64