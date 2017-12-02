# !/usr/bin/python

# Copyright (C) 2017 Pier Luigi Ventre, Stefano Salsano, Alessandro Masci - (CNIT and University of Rome "Tor Vergata")
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Deployment script for Mininet.
#
# @author Pier Luigi Ventre <pier.luigi.ventre@uniroma2.it>
# @author Stefano Salsano <stefano.salsano@uniroma2.it>
# @author Alessandro Masci <mascialessandro89@gmail.com>
#

from optparse import OptionParser
import argparse
from collections import defaultdict

# IPaddress dependency
from ipaddress import IPv6Network
import ipaddress

# Mininet
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSBridge, Node
from mininet.link import TCLink
from mininet.cli import CLI

# Utils
from utils import IPHost
# Routing
from routing import SPFRouting

import os
import json
import sys

import networkx as nx

from networkx.readwrite import json_graph

parser_path = "/home/user/workspace/Dreamer-Topology-Parser-and-Validator/"
if parser_path == "":
    print "Error : Set parser_path variable in srv6_mininet_extension.py"
    sys.exit(-2)
if not os.path.exists(parser_path):
    error("Error : parser_path variable in srv6_mininet_extension.py points to a non existing folder\n")
    sys.exit(-2)
sys.path.append(parser_path)

# Parser
from srv6_topo_parser import Srv6TopoParser

# Mapping host to vnfs
nodes_to_vnfs = defaultdict(list)
# Mapping node to management address
node_to_mgmt = {}
# Routes computed by the routing function
routes = defaultdict(list)
# Subnets to via
subnets_to_via = defaultdict(list)
# Network topology
topology = nx.MultiDiGraph()
# Interface to IP map
interfaces_to_ip = {}
# Default via
host_to_default_via = {}
# Vnfs file
VNF_FILE = "deployment/vnfs.json"
# nodes.sh file for setup of the nodes
NODES_SH = "deployment/nodes.sh"
# Routing file
ROUTING_FILE = "deployment/routing.json"
# Topology file
TOPOLOGY_FILE = "deployment/topology.json"
# Management Mask
MGMT_MASK = 64
# Data plane Mask
DP_MASK = 64
# Data plane soace
DP_SPACE = 56
# Vnf maks
VNF_MASK = 128


# Create Abilene topology and a management network for the hosts.
class Abilene(Topo):
    # Init of the topology
    def __init__(self, top="", **opts):
        # Init steps
        Topo.__init__(self, **opts)
       
        # Retrieves topology from json file
        topo = Srv6TopoParser(top, verbose=False, version=2)

        # We are going to use bw constrained links
        linkopts = dict(bw=1, delay=1000)

        # Create subnetting objects for assigning data plane addresses
        dataPlaneSpace = unicode('2001::0/%d' % DP_SPACE)
        dataPlaneNets = list(IPv6Network(dataPlaneSpace).subnets(new_prefix=DP_MASK))

        # Create subnetting objects for assigning mgmt plane addresses
        mgmtPlaneSpace = unicode('2000::0/%d' % MGMT_MASK)
        mgmtPlaneNet = list(IPv6Network(mgmtPlaneSpace).subnets(new_prefix=MGMT_MASK))[0]
        mgmtPlaneHosts = mgmtPlaneNet.hosts()

        # Define the routers representing the cities
        routers = topo.getRouters()
        # Define the host/servers representing the cities
        hosts = topo.getServers()
        # Define the edge links connecting hosts and routers
        edge_links = topo.getEdge()
        # Define the core links connecting routers
        core_links = topo.getCore()

        # Iterate on the routers and generate them
        for router in routers:
            # Assign mgmt plane IP
            mgmtIP = mgmtPlaneHosts.next()
            # Add the router to the topology
            self.addHost(
                name=router,
                cls=IPHost,
                sshd=True,
                mgmtip="%s/%s" % (mgmtIP, MGMT_MASK),
                vnfips=[]
            )
            # Save mapping node to mgmt
            node_to_mgmt[router] = str(mgmtIP)
            # Add node to the topology graph
            topology.add_node(router, mgmtip="%s/%s" % (mgmtIP, MGMT_MASK), type="router", group=200)

        # Create the mgmt switch
        br_mgmt = self.addSwitch('br-mgmt1', cls=OVSBridge)

        # Iterate on the hosts and generate them
        for host in hosts:
            # Define host group
            group = 100
            # Get the assinged vnfs
            host_vnfs = topo.getVnf(host)
            # Create an empty list
            vnfips = []
            # If the host has assigned vnfs
            if host_vnfs > 0:
                # Update group
                group = host_vnfs
                # Assign a data-plane net to the host
                net = dataPlaneNets.pop(0)
                # Get hosts iterator
                host_ips = net.hosts()
                # Iterate over the number of vnfs
                for index in range(host_vnfs):
                    # Add the ip to the set
                    vnfips.append("%s/%d" % (host_ips.next().exploded, VNF_MASK))
                # Save the destination
                subnets_to_via[str(net.exploded)].append(host)
                # Save the mapping nodes to vnfs
                nodes_to_vnfs[host] = vnfips
            # Assign mgmt plane IP
            mgmtIP = mgmtPlaneHosts.next()
            # Add the host to the topology
            self.addHost(
                name=host,
                cls=IPHost,
                sshd=True,
                mgmtip="%s/%s" % (mgmtIP, MGMT_MASK),
                vnfips=vnfips
            )
            # Save mapping node to mgmt
            node_to_mgmt[host] = str(mgmtIP)
            # Add node to the topology graph
            topology.add_node(host, mgmtip="%s/%s" % (mgmtIP, MGMT_MASK), type="server", group=group)

        # Assign the mgmt ip to the mgmt station
        mgmtIP = mgmtPlaneHosts.next()
        # Mgmt name
        mgmt = 'mgt'
        # Create the mgmt node in the root namespace
        self.addHost(
            name=mgmt,
            cls=IPHost,
            sshd=False,
            mgmtip="%s/%s" % (mgmtIP, MGMT_MASK),
            inNamespace=False
        )
        # Save mapping node to mgmt
        node_to_mgmt[mgmt] = str(mgmtIP)
        # Store mgmt in hosts
        hosts.append(mgmt)

        # Connect all the routers to the management network
        for router in routers:
            # Create a link between mgmt switch and the router
            self.addLink(router, br_mgmt, **linkopts)
            portNumber = self.port(router, br_mgmt)

        # Connect all the hosts/servers to the management network
        for host in hosts:
            # Create a link between mgmt switch and the host
            self.addLink(host, br_mgmt, **linkopts)
            portNumber = self.port(host, br_mgmt)

        # Iterate over the edge links and generate them
        for edge_link in edge_links:
            # The router is the left hand side of the pair
            router = edge_link[0]
            # The host is the right hand side of the pair
            host = edge_link[1]
            # Create the edge link
            self.addLink(router, host, **linkopts)
            # Get Port number
            portNumber = self.port(router, host)
            # Create lhs_intf
            lhs_intf = "%s-eth%d" % (router, portNumber[0])
            # Create rhs_intf
            rhs_intf = "%s-eth%d" % (host, portNumber[1])
            # Assign a data-plane net to this link
            net = dataPlaneNets.pop(0)
            # Get hosts on this subnet
            host_ips = net.hosts()
            # Get the default via
            default_via = "%s/%d" % (host_ips.next().exploded, DP_MASK)
            # Get the host ip
            host_ip = "%s/%d" % (host_ips.next().exploded, DP_MASK)
            # Map lhs_intf to ip
            interfaces_to_ip[lhs_intf] = default_via
            # Map rhs_intf to ip
            interfaces_to_ip[rhs_intf] = host_ip
            # Map host to default via
            host_to_default_via[host] = default_via
            # Add edge to the topology
            topology.add_edge(router, host, lhs_intf=lhs_intf, rhs_intf=rhs_intf, lhs_ip=default_via, rhs_ip=host_ip)
            # Add reverse edge to the topology
            topology.add_edge(host, router, lhs_intf=rhs_intf, rhs_intf=lhs_intf, lhs_ip=host_ip, rhs_ip=default_via)
            # Map subnets to router
            subnets_to_via[str(net.exploded)].append(router)
            # Map subnets to router
            subnets_to_via[str(net.exploded)].append(host)

        # Iterate over the core links and generate them
        for core_link in core_links:
            # Get the left hand side of the pair
            lhs = core_link[0]
            # Get the right hand side of the pair
            rhs = core_link[1]
            # Create the core link
            self.addLink(lhs, rhs, **linkopts)
            # Get Port number
            portNumber = self.port(lhs, rhs)
            # Create lhs_intf
            lhs_intf = "%s-eth%d" % (lhs, portNumber[0])
            # Create rhs_intf
            rhs_intf = "%s-eth%d" % (rhs, portNumber[1])
            # Assign a data-plane net to this link
            net = dataPlaneNets.pop(0)
            # Get hosts on this subnet
            host_ips = net.hosts()
            # Get lhs_ip
            lhs_ip = "%s/%d" % (host_ips.next().exploded, DP_MASK)
            # Get rhs_ip
            rhs_ip = "%s/%d" % (host_ips.next().exploded, DP_MASK)
            # Map lhs_intf to ip
            interfaces_to_ip[lhs_intf] = lhs_ip
            # Map rhs_intf to ip
            interfaces_to_ip[rhs_intf] = rhs_ip
            # Add edge to the topology
            topology.add_edge(lhs, rhs, lhs_intf=lhs_intf, rhs_intf=rhs_intf, lhs_ip=lhs_ip, rhs_ip=rhs_ip)
            # Add the reverse edge to the topology
            topology.add_edge(rhs, lhs, lhs_intf=rhs_intf, rhs_intf=lhs_intf, lhs_ip=rhs_ip, rhs_ip=lhs_ip)
            # Map subnet to lhs
            subnets_to_via[str(net.exploded)].append(lhs)
            # Map subnet to rhs
            subnets_to_via[str(net.exploded)].append(rhs)

# Utility function to dump relevant information of the emulation
def dump():
  # Json dump of the topology
  with open(TOPOLOGY_FILE, 'w') as outfile:
    # Get json topology
    json_topology = json_graph.node_link_data(topology)
    # Convert links

    json_topology['links'] = [
        {
            'source': json_topology['nodes'][link['source']]['id'],
            'target': json_topology['nodes'][link['target']]['id'],
            'lhs_intf': link['lhs_intf'],
            'rhs_intf': link['rhs_intf'],
#            'lhs_ip': link['lhs_ip'],
            'lhs_ip': str((ipaddress.ip_interface(link['lhs_ip'])).ip),
#            'rhs_ip': link['rhs_ip']
            'rhs_ip': str((ipaddress.ip_interface(link['rhs_ip'])).ip)
        }
        for link in json_topology['links']]
    # Dump the topology
    json.dump(json_topology, outfile, sort_keys = True, indent = 2)
  # Json dump of the routing
  with open(ROUTING_FILE, 'w') as outfile:
    json.dump(routes, outfile, sort_keys = True, indent = 2)
  # Dump for nodes.sh
  with open(NODES_SH, 'w') as outfile:
    # Create header
    nodes = "declare -a NODES=("
    # Iterate over management ips
    for node, ip in node_to_mgmt.iteritems():
      # Add the nodes one by one
      nodes = nodes + "%s " % ip
    # Eliminate last character
    nodes = nodes[:-1] + ")\n"
    # Write on the file
    outfile.write(nodes)
    # Json dump of the vnfs
  with open(VNF_FILE, 'w') as outfile:
    json.dump(nodes_to_vnfs, outfile, sort_keys = True, indent = 2)

# Utility function to shutdown the emulation
def shutdown():
    # Clean Mininet emulation environment
    os.system('sudo mn -c')
    # Clean Mininet emulation environment
    os.system('sudo killall sshd')

# Utility function to deploy Mininet topology
def deploy(options):
    # Retrieves options
    controller = options.controller
    topologyFile = options.topology
    # Create routing
    routing = SPFRouting()
    # Set Mininet log level to info
    setLogLevel('info')
    # Create Mininet topology
    topo = Abilene(
        top=topologyFile
    )
    # Create Mininet net
    net = Mininet(
        topo=topo,
        link=TCLink,
        build=False,
        controller=None,
    )
    # Add manually external controller
    net.addController("c0", controller=RemoteController, ip=controller)
    # Build topology
    net.build()
    # Start topology
    net.start()
    # Build routing
    routing.routing(routes, topology, subnets_to_via, interfaces_to_ip)
    # Iterate over the mininet hosts (routers, servers, mgt)
    for host in net.hosts:
        # Get the default via, if exists
        default_via = host_to_default_via.get(host.name, None)
        # Get the subnets, if exists
        subnets = routes.get(host.name, [])
        # Configure v6 addresses
        host.configv6(interfaces_to_ip, default_via, subnets)
    # Dump relevant information
    dump()
    # Mininet CLI
    CLI(net)
    # Stop topology
    net.stop()

# Parse command line options and dump results
def parseOptions():
    parser = OptionParser()
    # IP of RYU controller
    parser.add_option('--controller', dest='controller', type='string', default="127.0.0.1",
                      help='IP address of the Controlle instance')
    # Topology json file
    parser.add_option('--topology', dest='topology', type='string', default="example_network_abilene.json",
                      help='Topology file')
    # Parse input parameters
    (options, args) = parser.parse_args()
    # Done, return
    return options


if __name__ == '__main__':
    # Let's parse input parameters
    opts = parseOptions()
    # Deploy topology
    deploy(opts)
    # Clean shutdown
    shutdown()