"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");
const { pathToFileURL } = require("node:url");

const { isPathWithin, localFileAllowed } = require("../local_file_policy.cjs");

test("allows only files inside an explicit root", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "seo-geo-report-"));
  fs.mkdirSync(path.join(root, "assets"));
  fs.writeFileSync(path.join(root, "report.html"), "report");
  fs.writeFileSync(path.join(root, "assets", "logo.svg"), "logo");
  assert.equal(isPathWithin(root, path.join(root, "assets", "logo.svg")), true);
  assert.equal(isPathWithin(root, path.join(root, "..", "secret.txt")), false);
  assert.equal(localFileAllowed(pathToFileURL(path.join(root, "report.html")).href, [root]), true);
  assert.equal(localFileAllowed(pathToFileURL(path.join(root, "..", "secret.txt")).href, [root]), false);
  fs.rmSync(root, { recursive: true, force: true });
});

test("rejects symlinks that escape an allowed root", () => {
  const parent = fs.mkdtempSync(path.join(os.tmpdir(), "seo-geo-symlink-"));
  const root = path.join(parent, "report");
  const secret = path.join(parent, "secret.txt");
  fs.mkdirSync(root);
  fs.writeFileSync(secret, "secret");
  fs.symlinkSync(secret, path.join(root, "asset.txt"));
  assert.equal(localFileAllowed(pathToFileURL(path.join(root, "asset.txt")).href, [root]), false);
  fs.rmSync(parent, { recursive: true, force: true });
});

test("rejects malformed and non-file URLs", () => {
  assert.equal(localFileAllowed("https://example.com/font.woff2", [os.tmpdir()]), false);
  assert.equal(localFileAllowed("file://%", [os.tmpdir()]), false);
});
