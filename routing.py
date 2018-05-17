#!/usr/bin/python

##############################################################################################
# Copyright (C) 2017 Pier Luigi Ventre - (CNIT and University of Rome "Tor Vergata")
# Copyright (C) 2017 Stefano Salsano - (CNIT and University of Rome "Tor Vergata")
# Copyright (C) 2017 Alessandro Masci - (University of Rome "Tor Vergata")
# www.uniroma2.it/netgroup - www.cnit.it
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
# Routing module for Segment Routing IPv6
#
# @author Pier Luigi Ventre <pierventre@hotmail.com>
# @author Stefano Salsano <stefano.salsano@uniroma2.it>
# @author Alessandro Masci <mascialessandro89@gmail.com>

from collections import defaultdict
from mininet.log import info

import networkx as nx
import time

# Build shortest path routing for the given topology
class SPFRouting( object ):

  def routing(self, routes, topology, destinations, interfaces_to_ip):
    # Init steps
    info("Building routing...\n")
    # Calculate all the shortest path for the given topology
    shortest_paths = nx.all_pairs_shortest_path(topology)
    # Iterate over nodes
    for node in topology.nodes(data=True):
      # Access to data
      node_type   = node[1]['type']
      # Access to name
      node        = node[0]
      # This node is a server
      if node_type == "server":
        # Just skip
        continue
      # Iterate over destinations:
      for destination, via in destinations.iteritems():
        # If it is directly attached
        if node in via:
          # Just skip
          continue
        # Log the procedure
        info("Calculating route from " + node + " -> " + destination + "...")
        # Initialize min via
        min_via = via[0]
        # Iterate over remaining via
        for i in range(1, len(via)):
          # Get hops of the old via
          old_hops      = len(shortest_paths[node][min_via])
          # Get hops of the current via
          current_hops  = len(shortest_paths[node][via[i]])
          # Lower
          if current_hops < old_hops:
            # Update min_via
            min_via = via[i]
        # Init route
        route = {}
        # Save the destination
        route["subnet"]   = destination
        # Get the link from the topology
        link_topology     = topology[node][shortest_paths[node][min_via][1]]
        # Get the gateway. We are assuming no multi-links
        gateway           = interfaces_to_ip[link_topology[0]["rhs_intf"]]
        # Save the gateway
        route["gateway"]  = gateway
        # Get the device
        route["device"]   = link_topology[0]["lhs_intf"]
        # Save the route
        routes[node].append(route)
        # Log the found via
        info("found " + gateway + "\n")
    # Done
    return routes 
