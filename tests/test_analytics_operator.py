"""Verify boardgame GA4 operator classification without sending analytics requests."""
import json
import shutil
import subprocess

import pytest

from scripts import build_site


def test_automatic_pageview_receives_operator_parameter():
    source = build_site.ANALYTICS
    assert 'gtag("config",id,{operator_test:op?"1":"0"})' in source
    assert 'gtag("config",id)' not in source
    assert 'gtag("event","page_view"' not in source


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js unavailable")
def test_operator_parameter_persists_and_resets_in_browser_commands():
    # Run the actual generated JS with a minimal browser mock. No network requests.
    harness = r"""
const assert = require("node:assert/strict");
const vm = require("node:vm");
const source = JSON.parse(process.argv[1]);

function visit(query, local, expected) {
  const commands = [];
  const ctx = {
    KYO_BODO_CONFIG: {gaMeasurementId: "G-Q1N14V276G"},
    location: {search: query, pathname: "/kyo-bodo-jp/diagnosis/"},
    URLSearchParams,
    localStorage: {
      getItem: key => local.has(key) ? local.get(key) : null,
      setItem: (key, value) => local.set(key, value),
      removeItem: key => local.delete(key)
    },
    sessionStorage: {getItem: () => null, setItem: () => {}},
    document: {
      createElement: () => ({}),
      head: {appendChild: () => {}},
      addEventListener: () => {}
    },
    dataLayer: commands
  };
  ctx.window = ctx;
  vm.runInNewContext(source, ctx, {timeout: 1000});
  const config = commands.filter(c => c[0] === "config");
  assert.equal(config.length, 1, "only one automatic pageview config");
  assert.equal(config[0][1], "G-Q1N14V276G");
  assert.equal(config[0][2].operator_test, expected, "pageview operator tag");
  assert.equal(commands.filter(c => c[0] === "event" && c[1] === "page_view").length, 0, "no duplicated manual pageview");
  ctx.kyoTrack("diagnosis_complete", {players: 2});
  const event = commands.find(c => c[0] === "event" && c[1] === "diagnosis_complete");
  assert.equal(event[2].operator_test, expected, "custom action tag stays correct");
  assert.equal(event[2].page_path, "/kyo-bodo-jp/diagnosis/");
}
const local = new Map();
visit("?test=1", local, "1");
visit("", local, "1");
visit("?test=0", local, "0");
visit("", local, "0");
visit("", new Map(), "0");
"""
    result = subprocess.run(
        ["node", "-e", harness, json.dumps(build_site.ANALYTICS)],
        capture_output=True, text=True, check=False, timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr
