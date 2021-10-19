//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
// 
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
// 

#pragma once

#include "inet/common/InitStages.h"
#include "artery/application/Middleware.h"
#include "artery/utility/IdentityRegistry.h"

#include "crownet/applications/common/AppFsm.h"
#include "crownet/applications/common/BaseApp.h"
#include "crownet/applications/dmap/dmap_m.h"
#include "crownet/common/IDensityMapHandler.h"
#include "crownet/common/converter/OsgCoordConverter.h"
#include "crownet/common/util/FileWriter.h"
#include "crownet/dcd/regularGrid/RegularDcdMap.h"
#include "crownet/dcd/generic/CellVisitors.h"
#include "crownet/dcd/regularGrid/RegularCell.h"

using namespace omnetpp;
using namespace inet;


namespace crownet {
class BaseDensityMapApp : public BaseApp,
                          public IDensityMapHandler<RegularDcdMap>
                          {
public:
    virtual ~BaseDensityMapApp();
    BaseDensityMapApp(){};


protected:
 // cSimpleModule
 virtual int numInitStages() const override { return NUM_INIT_STAGES; }
 virtual void initialize(int stage) override;

 virtual void finish() override;


 virtual FsmState handleDataArrived(Packet *packet) override;

 //
 virtual Packet *createPacket() override;

 // FSM
 virtual FsmState fsmSetup(cMessage *msg) override;
 virtual FsmState fsmAppMain(cMessage *msg) override;

 // App logic
 virtual void initDcdMap();
 virtual void initWriter();
 virtual bool mergeReceivedMap(Packet *packet);

 // IDensityMapHandler
 // update map with data from neighborhood table
 virtual void updateLocalMap() override;
 virtual void computeValues() override;
 virtual void writeMap() override;
 virtual std::shared_ptr<RegularDcdMap> getMap() override;
 virtual void setCoordinateConverter(std::shared_ptr<OsgCoordinateConverter> converter) override;
 virtual void setMapFactory(std::shared_ptr<RegularDcdMapFactory>) override;

 // AppStatusInfo
 virtual const bool canProducePacket() override;
 virtual const inet::b getMinPdu() override;
protected:

 std::shared_ptr<GridCellIDKeyProvider> cellProvider;
 std::shared_ptr<OsgCoordinateConverter> converter;
 std::shared_ptr<RegularDcdMapFactory> dcdMapFactory;

 std::shared_ptr<RegularDcdMap> dcdMap;
 std::unique_ptr<FileWriter> fileWriter;
 std::shared_ptr<TimestampedGetEntryVisitor<RegularCell>> valueVisitor;
 simtime_t lastUpdate = -1.0;
 MapCfg *mapCfg;
 RegularGridInfo grid;


 RegularDcdMapWatcher* dcdMapWatcher;
 cMessage *localMapTimer;
 cPar *localMapUpdateInterval;

};

} // namesapce crownet
