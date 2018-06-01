#!/usr/bin/python

##############################################################################################
# Copyright (C) 2018 Pier Luigi Ventre - (CNIT and University of Rome "Tor Vergata")
# Copyright (C) 2018 Stefano Salsano - (CNIT and University of Rome "Tor Vergata")
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
# Net utils for Segment Routing IPv6
#
# @author Pier Luigi Ventre <pierventre@hotmail.com>
# @author Stefano Salsano <stefano.salsano@uniroma2.it>

from ipaddress import IPv6Network, IPv4Network

# Allocates mgmt address
class MgmtAllocator(object):

  bit = 64
  net = unicode("2000::/%d" % bit)
  prefix = 64

  def __init__(self): 
    print "*** Calculating Available Mgmt Addresses"
    self.mgmtnet = (IPv6Network(self.net)).hosts()
  
  def nextMgmtAddress(self):
    n_host = next(self.mgmtnet)
    return n_host.__str__()