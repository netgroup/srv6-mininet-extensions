# SRv6 Mininet extensions  #

This project creates Mininet networks for testing the SRv6 technology

### Prerequisite ###

This project depends on [Dreamer Topology Parser and Validator](https://github.com/netgroup/Dreamer-Topology-Parser)

    > git clone https://github.com/netgroup/Dreamer-Topology-Parser
    > sudo python setup.py install

This project depends on [SRv6 Properties Generators](https://github.com/netgroup/srv6-properties-generators)

    > git clone https://github.com/netgroup/srv6-properties-generators
    > sudo python setup.py install

### Run an example experiment ###

**--help** for usage options:

    Usage: srv6_mininet_extension.py [options]

    Options:
    -h, --help            show this help message and exit
    --controller=CONTROLLER
                        IP address of the Controller instance
    --topology=TOPOLOGY   Topology file

You can start a topology just providing a topology file (relative path):

    > sudo ./srv6_mininet_extensions.py --topology topo/example_srv6_topology.json

now you have started the topology defined in the file example_srv6_topology.json.json (3 SRv6 routers)

The file topology.json in the /tmp folder provides a dump of the topology with IPv6 addresses: 

    > cat /tmp/topology.json

for example you can find the mgmt ip of the nodes: 

    "id": "sur1", "mgmtip": "2000::3/64"
    "id": "ads2", "mgmtip": "2000::2/64"
    "id": "ads1", "mgmtip": "2000::1/64", 

or you can get information about links:

    "lhs_intf": "sur1-eth2", "lhs_ip": "2001:0:0:2::2", 
    "rhs_intf": "ads2-eth2", "rhs_ip": "2001:0:0:2::1", 

Each router has a management interface eth0 connected "out of band" with the host running mininet. You can login on any router using their management IP, for example login in the ads1 router and ping/traceroute the ads2 router:

    # Connect to the node ads1
    > ssh root@2000::1

    # Ping ads2 router 2001:0:0:2::1
    > ping -6 2001:0:0:2::1
    > PING 2001:0:0:2::1(2001:0:0:2::1) 56 data bytes
    > 64 bytes from 2001:0:0:2::1: icmp_seq=1 ttl=64 time=5.04 ms
    > 64 bytes from 2001:0:0:2::1: icmp_seq=2 ttl=64 time=2.67 ms
    > 64 bytes from 2001:0:0:2::1: icmp_seq=3 ttl=64 time=2.72 ms
    > 64 bytes from 2001:0:0:2::1: icmp_seq=4 ttl=64 time=2.62 ms
    > 64 bytes from 2001:0:0:2::1: icmp_seq=5 ttl=64 time=2.68 ms

    # Traceroute ads2 router 2001:0:0:2::1 
    > traceroute -6 2001:0:0:2::1
    > traceroute to 2001:0:0:2::1 (2001:0:0:2::1), 30 hops max, 80 byte packets
    > 1  2001:0:0:2::1 (2001:0:0:2::1)  2.584 ms  2.487 ms  2.408 ms
    
Now you can add SRv6 policies:

    # Connect to the ads1 host
    > ssh root@2000::1

    # Traffic towards 2001:0:0:d::1 is steered through 2001::3
    > ip -6 r a 2001:0:0:2::1/128 encap seg6 mode encap segs 2002::3 dev ads1-eth1

    # Ping ads2 router 2001:0:0:2::1
    > ping -6 2001:0:0:2::1
    > PING 2001:0:0:2::1(2001:0:0:2::1) 56 data bytes
    > 64 bytes from 2001:0:0:2::1: icmp_seq=1 ttl=64 time=1.60 ms
    > 64 bytes from 2001:0:0:2::1: icmp_seq=2 ttl=64 time=1.99 ms
    > 64 bytes from 2001:0:0:2::1: icmp_seq=3 ttl=64 time=2.00 ms
    > 64 bytes from 2001:0:0:2::1: icmp_seq=4 ttl=64 time=1.99 ms
    > 64 bytes from 2001:0:0:2::1: icmp_seq=5 ttl=64 time=1.97 ms

    # Traceroute ads2 router 2001:0:0:2::1 
    > traceroute -6 2001:0:0:2::1
    > traceroute to 2001:0:0:2::1 (2001:0:0:2::1), 30 hops max, 80 byte packets
    > 1  2001:0:0:1::2 (2001:0:0:1::2)  2.122 ms  2.052 ms  2.031 ms
    > 2  2001:0:0:2::1 (2001:0:0:2::1)  1.502 ms  1.485 ms  1.469 ms

    # Dump the traffic on the outgoing interface
    > sudo tcpdump -nei ads1-eth2
    > tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    > listening on ads1-eth2, link-type EN10MB (Ethernet), capture size 262144 bytes
    > 17:41:11.513902 22:9b:8e:4a:77:6f > d2:27:1b:74:c6:f1, ethertype IPv6 (0x86dd), length 182: 2002::1 > 2002::3: srcrt (len=2, type=4, segleft=0[|srcrt]
    > 17:41:12.516220 22:9b:8e:4a:77:6f > d2:27:1b:74:c6:f1, ethertype IPv6 (0x86dd), length 182: 2002::1 > 2002::3: srcrt (len=2, type=4, segleft=0[|srcrt]
    > 17:41:13.517563 22:9b:8e:4a:77:6f > d2:27:1b:74:c6:f1, ethertype IPv6 (0x86dd), length 182: 2002::1 > 2002::3: srcrt (len=2, type=4, segleft=0[|srcrt]
    
    # Dump the traffic on the incoming interface
    > sudo tcpdump -nei ads1-eth1
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on ads1-eth1, link-type EN10MB (Ethernet), capture size 262144 bytes
    17:41:00.503046 2a:64:43:95:3c:08 > d6:3b:b2:61:71:8f, ethertype IPv6 (0x86dd), length 118: 2001:0:0:2::1 > 2001::1: ICMP6, echo reply, seq 14, length 64
    17:41:01.503871 2a:64:43:95:3c:08 > d6:3b:b2:61:71:8f, ethertype IPv6 (0x86dd), length 118: 2001:0:0:2::1 > 2001::1: ICMP6, echo reply, seq 15, length 64
    17:41:02.504828 2a:64:43:95:3c:08 > d6:3b:b2:61:71:8f, ethertype IPv6 (0x86dd), length 118: 2001:0:0:2::1 > 2001::1: ICMP6, echo reply, seq 16, length 64
