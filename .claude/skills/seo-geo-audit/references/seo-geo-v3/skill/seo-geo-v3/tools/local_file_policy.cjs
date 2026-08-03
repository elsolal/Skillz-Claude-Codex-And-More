"use strict";

const fs = require("fs");
const path = require("path");
const { fileURLToPath } = require("url");

function isPathWithin(root, candidate) {
  const relative = path.relative(path.resolve(root), path.resolve(candidate));
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

function localFileAllowed(url, allowedRoots) {
  let candidate;
  try {
    candidate = fs.realpathSync(fileURLToPath(url));
  } catch (_error) {
    return false;
  }
  return allowedRoots.some((root) => {
    try {
      return isPathWithin(fs.realpathSync(root), candidate);
    } catch (_error) {
      return false;
    }
  });
}

module.exports = { isPathWithin, localFileAllowed };
