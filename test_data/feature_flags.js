'use strict';

const semver = require('semver');

class FeatureFlags {
  // OldVersion is optional and used in case of upgrade.
  // It resambles the version we are upgradeing from
  // Current is the version of the database we are attached to
  constructor(currentVersion, oldVersion = "") {
    if (oldVersion === "") {
      oldVersion = currentVersion;
    }
    this._old = semver.parse(semver.coerce(oldVersion));
    this._current = semver.parse(semver.coerce(currentVersion));
  }

  hasSmartGraphValidator() {
    return semver.gte(this._current, "3.9.0");
  }

  shouldValidateOneShard() {
    return semver.gte(this._old, "3.7.7");
  }
  shouldValidateFoxx() {
    return semver.gte(this._old, "3.6.0");
  }
};

exports.FeatureFlags = FeatureFlags;
