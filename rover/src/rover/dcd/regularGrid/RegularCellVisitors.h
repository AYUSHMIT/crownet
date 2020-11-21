/*
 * RegularCellVisitor.h
 *
 *  Created on: Nov 23, 2020
 *      Author: sts
 */

#pragma once

#include "rover/dcd/generic/CellVisitors.h"
#include "rover/dcd/regularGrid/RegularCell.h"

namespace rover {
// test only makes no sense to increment all IEntries
class IncrementerVisitor : public TimestampedVisitor<RegularCell> {
 public:
  IncrementerVisitor(RegularCell::time_t time)
      : TimestampedVisitor<RegularCell>(time) {}
  virtual void applyTo(RegularCell& cell) override {
    for (auto e : cell) {
      e.second->incrementCount(time);
    }
  }
};

/**
 * Reset all IEntries within a RegularCell
 */
class ResetVisitor : public TimestampedVisitor<RegularCell> {
 public:
  ResetVisitor(RegularCell::time_t time)
      : TimestampedVisitor<RegularCell>(time) {}
  virtual void applyTo(RegularCell& cell) override {
    for (auto e : cell) {
      e.second->reset(time);
    }
  }
};

/**
 * Clear all IEntries within a RegularCell
 */
class ClearVisitor : public TimestampedVisitor<RegularCell> {
 public:
  ClearVisitor(RegularCell::time_t time)
      : TimestampedVisitor<RegularCell>(time) {}
  virtual void applyTo(RegularCell& cell) override {
    for (auto e : cell) {
      e.second->clear(time);
    }
  }
};

/**
 * Return Youngest Measurement from a RegularCell
 *
 * Only look at valid items.
 */
class YmfVisitor : public GetEntryVisitor<RegularCell> {
 public:
  virtual RegularCell::entry_t_ptr applyTo(
      const RegularCell& cell) const override;
  virtual std::string getName() const override { return "ymf"; }
};

// class LocalVisitor : public GetCellVisitor<RegularCell> {
// public:
//  virtual RegularCell::value_type applyTo(
//      const RegularCell& cell) const override;
//};

/**
 * todo: Return mean measurement with all cells weighted equally
 */
// Implement ...

/**
 * todo: Return mean measurement with weighted based on the distance between the
 * cell origin and the Entry owner
 */
// Implement ...

class AlgBiggest : public GetEntryVisitor<RegularCell> {
 public:
  virtual RegularCell::entry_t_ptr applyTo(
      const RegularCell& cell) const override;
};

class AlgSmall : public GetEntryVisitor<RegularCell> {
 public:
  virtual RegularCell::entry_t_ptr applyTo(
      const RegularCell& cell) const override;
};
}  // namespace rover
