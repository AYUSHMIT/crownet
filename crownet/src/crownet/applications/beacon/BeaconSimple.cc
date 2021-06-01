/*
 * BeaconSimple.cc
 *
 *  Created on: Jan 23, 2021
 *      Author: sts
 */

#include "crownet/applications/beacon/BeaconSimple.h"
#include "crownet/applications/beacon/Beacon_m.h"
#include "inet/common/ModuleAccess.h"

namespace crownet {

Define_Module(BeaconSimple)

BeaconSimple::BeaconSimple() {}

// cSimpleModule
void BeaconSimple::initialize(int stage) {
    BaseApp::initialize(stage);
    if (stage == INITSTAGE_LOCAL){
        mobility = inet::getModuleFromPar<inet::IMobility>(par("mobilityModule"), inet::getContainingNode(this));
        nTable = inet::getModuleFromPar<NeighborhoodTable>(par("neighborhoodTableMobdule"), inet::getContainingNode(this));
        hostId = getContainingNode(this)->getId();
        WATCH(hostId);
    }
}

// FSM
FsmState BeaconSimple::fsmAppMain(cMessage *msg) {

    const auto &beacon = createPacket<BeaconPacket>(B(224)); //64+64+64+32
    beacon->setTime(simTime());
    beacon->setPos(mobility->getCurrentPosition());
    beacon->setNodeId(hostId);

    sendPayload(beacon);
    scheduleNextAppMainEvent();
    return FsmRootStates::WAIT_ACTIVE;
}

FsmState BeaconSimple::handleDataArrived(Packet *packet){
    auto p = packet->popAtFront<BeaconPacket>();

    NeighborhoodTableEntry b{p->getNodeId(), p->getTime(), simTime(), p->getPos(), p->getEpsilon()};
    nTable->handleBeacon(std::move(b));
    return FsmRootStates::WAIT_ACTIVE;
}


} /* namespace crownet */
