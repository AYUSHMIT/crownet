/*
 * NedFunctions.h
 *
 *  Created on: Dec 10, 2020
 *      Author: sts
 */

#include <omnetpp/cnedvalue.h>
#include "inet/common/INETDefs.h"

using namespace omnetpp;

namespace rover {

namespace utils {

cNEDValue nedf_ifTrueOrElse(cComponent *context, cNEDValue argv[], int argc) {
  if (argv[0].getType() != cNEDValue::BOOL)
    throw cRuntimeError("useOrElse(): bool arguments expected");
  bool pred = argv[0].boolValue();
  if (pred) {
    return argv[1];
  } else {
    return argv[2];
  }
}

Define_NED_Function2(
    nedf_ifTrueOrElse,
    "string ifTrueOrElse(bool pred, string first, string second)", "misc",
    "if pred is true return first else second.");

}  // namespace utils
}  // namespace rover
