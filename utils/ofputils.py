def add_flow(datapath, priority, match, actions, buffer_id=None):
    print 'add flows'
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser

    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

    if buffer_id:
        mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                priority=priority, match=match,
                                idle_timeout=15, instructions=inst)
    else:
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                idle_timeout=15, match=match, instructions=inst)
    datapath.send_msg(mod)

def set_meter_entry(datapath, bandwidth, id, mod):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        command = None
        if mod == 'ADD':
            command = ofproto.OFPMC_ADD
            add_flow_meta(datapath, 10, id, id)
        elif mod == 'MODIFY':
            command = ofproto.OFPMC_MODIFY
        elif mod == 'DELETE':
            command = ofproto.OFPMC_DELETE

        # Policing for Scavenger class
        band = parser.OFPMeterBandDrop(rate=bandwidth,
                                       burst_size=1024)
        req = parser.OFPMeterMod(datapath, command,
                                 ofproto.OFPMF_KBPS, id, [band])
        datapath.send_msg(req)
        # add_flow_meta(datapath, 10, id, id)

def add_flow_for_ratelimite(datapath, priority, match, actions, meter, state, buffer_id=None):
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser
    inst = []
    if state == 'up':
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                parser.OFPInstructionWriteMetadata(int(meter), 4294967295),
                parser.OFPInstructionGotoTable(1)]
    else:
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

    if buffer_id:
        mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                priority=priority, match=match,
                                idle_timeout=15, instructions=inst)
    else:
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                idle_timeout=15, match=match, instructions=inst)
    datapath.send_msg(mod)

def add_flow_meta(datapath, priority, meta, meter_id, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(metadata = meta)
        inst = [parser.OFPInstructionMeter(meter_id)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, table_id=1, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, table_id=1, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)
