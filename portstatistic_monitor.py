"""Project For Port Monitor on switches."""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.topology.api import get_switch
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.lib import hub

from setting.db.data_collection import switch_stat

import logging
import time
import datetime

class PortStatMonitor(app_manager.RyuApp):

    """Class for Port Monitor."""

    def __init__(self, *args, **kwargs):
        """Initial method."""
        super(PortStatMonitor, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        self.monitor_thread = hub.spawn(self._monitor)
        hdlr = logging.FileHandler('sdn_log.log')
        self.logger.addHandler(hdlr)

    def _monitor(self):
        while True:
            switch_list = get_switch(self.topology_api_app, None)
            for datapath in switch_list:
                self._update_sw_stas(datapath)
                self._request_stats(datapath.dp)
            hub.sleep(5)

    def _update_sw_stas(self, datapath):
        """Update statistics for switches method."""
        # Initialization
        if switch_stat.get(datapath.dp.id) is None:
            alive_ports = []
            switch_stat.update({datapath.dp.id: {'alive_port': alive_ports}})

        # Update active ports in list
        alive_port_list = switch_stat.get(datapath.dp.id).get('alive_port')
        for port in datapath.ports:
            if port.is_live():
                if port.port_no not in alive_port_list:
                    alive_port_list.append(port.port_no)
            else:
                if port.port_no in alive_port_list:
                    alive_port_list.remove(port.port_no)
                    if switch_stat.get(datapath.dp.id).get('stats').get(port.port_no) is not None:
                        p_stat = switch_stat.get(datapath.dp.id).get('stats')
                        p_stat[port.port_no] = None

    def _request_stats(self, datapath):
        """Send PortStatsRequest method."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        """Handle PortStatsReply from switches method."""
        sw_dpid = ev.msg.datapath.id
        self.logger.info('-----------')
        self.logger.info(ev.msg.datapath.id)
        self.logger.info('-----------')

        # Initialization
        if switch_stat.get(sw_dpid).get('stats') is None:
            switch_stat.get(sw_dpid).update({'stats': {}})
        if switch_stat.get(sw_dpid).get('weight') is None:
            switch_stat.get(sw_dpid).update({'weight': {}})
        if switch_stat.get(sw_dpid).get('cost') is None:
            switch_stat.get(sw_dpid).update({'cost': 0.0})

        r = 0
        t = 0
        e = 0
        for stat in ev.msg.body:
            if stat.port_no in switch_stat.get(sw_dpid).get('alive_port'):
                # Claculate statistics on each active port
                self.logger.info(stat.port_no)
                conter_list = [stat.port_no, stat.rx_bytes, stat.tx_bytes, stat.rx_dropped, stat.tx_dropped, stat.rx_errors, stat.tx_errors, stat.collisions]
                port_stat = {stat.port_no: conter_list}



                if switch_stat.get(sw_dpid).get('stats').get(stat.port_no) is not None:

                    his_stat = switch_stat.get(sw_dpid).get('stats').get(stat.port_no)
                    self.logger.info('%s %s', conter_list, his_stat)
                    self.logger.info('rx_byte %d', (conter_list[1] - his_stat[1])/5)
                    self.logger.info('tx_byte %d', (conter_list[2] - his_stat[2])/5)
                    self.logger.info('drop %d', (conter_list[3] - his_stat[3])/5)
                    r = r + (conter_list[1] - his_stat[1])/5
                    t = t + (conter_list[2] - his_stat[2])/5
                    e = e + (conter_list[3] - his_stat[3])/5

                weight_list = [r, t, e]
                port_weight = {stat.port_no: weight_list}

                # Update port statistics
                sw_stat = switch_stat.get(sw_dpid).get('stats')
                sw_stat.update(port_stat)
                sw_weight = switch_stat.get(sw_dpid).get('weight')
                sw_stat.update(port_weight)

                self.logger.info('=======')


        self.logger.info('cost function r : %d',r)
        self.logger.info('cost function t : %d',t)
        self.logger.info('cost function r-t: %d',r-t)
        self.logger.info('cost function d: %d',e)
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        self.logger.info('time %s', st)

        pp = r-t
        if r != 0:
            self.logger.info('cost function: %f',float(pp)/float(r))
            switch_stat.get(sw_dpid).update({'cost': float(pp)/float(r)})
