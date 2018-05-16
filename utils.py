#!/usr/bin/python

#
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
# New mininet abstractions.
#
# @author Pier Luigi Ventre <pier.luigi.ventre@uniroma2.it>
# @author Stefano Salsano <stefano.salsano@uniroma2.it>
# @author Alessandro Masci <mascialessandro89@gmail.com>
#

# Mininet
from mininet.node import Host, OVSSwitch

import re

# Abstraction to model an augmented Host with a default via
class IPHost(Host):

  def __init__(self, name, *args, **kwargs):
    dirs = ['/var/mininet']
    Host.__init__(self, name, privateDirs=dirs, *args, **kwargs)

  def config(self, **kwargs):
    # Init steps
    Host.config(self, **kwargs)
    # Iterate over the interfaces
    first = True
    for intf in self.intfs.itervalues():
      # Remove any configured address
      self.cmd('ifconfig %s 0' %intf.name)
      # For the first one, let's configure the mgmt address
      if first:
        first = False
        self.cmd('ip a a %s dev %s' %(kwargs['mgmtip'], intf.name))
    # Configure the loopback address
    if kwargs.get('loopbackip',None):
      self.cmd('ip a a %s dev lo' %(kwargs['loopbackip']))
    #let's write the hostname in /var/mininet/hostname
    self.cmd("echo '" + self.name + "' > /var/mininet/hostname")
    # If requested
    if kwargs['sshd']:
      # Let's start sshd daemon in the hosts
      self.cmd('/usr/sbin/sshd -D &')

  def configv6(self, interfaces_to_ip, default_via, subnets):
    # Enable IPv6 forwarding
    self.cmd("sysctl -w net.ipv6.conf.all.forwarding=1")
    # Enable SRv6 on the interface
    self.cmd("sysctl -w net.ipv6.conf.all.seg6_enabled=1")
    # Iterate over the interfaces
    for intf in self.intfs.itervalues():
      # Enable IPv6 forwarding
      self.cmd("sysctl -w net.ipv6.conf.%s.forwarding=1" %intf.name)
      # Enable SRv6 on the interface
      self.cmd("sysctl -w net.ipv6.conf.%s.seg6_enabled=1" %intf.name)
      # Get the associated ip
      ip = interfaces_to_ip.get(intf.name, None)
      # If association exists
      if ip:
        # Configure the related IPv6 for that link
        self.cmd('ip a a %s dev %s' %(ip, intf.name))
        # Check if the default via exist
        if default_via:
          # Get the default via ip
          default_via_ip = default_via.split("/")[0]
          # Add default via
          self.cmd('ip r a default via %s dev %s' %(default_via_ip, intf.name))
    # Iterate over the reachable subnets
    for subnet in subnets:
      # Get the gateway ip
      gateway_ip = subnet['gateway'].split("/")[0]
      # Add static route
      self.cmd('ip r a %s via %s dev %s' %(subnet['subnet'], gateway_ip, subnet['device']))
