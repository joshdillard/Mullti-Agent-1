/**
 * Note: When using the Node.JS APIs, the config file
 * doesn't apply. Instead, pass options directly to the APIs.
 *
 * All configuration options: https://remotion.dev/docs/config
 */

import { Config } from "@remotion/cli/config";
import { enableTailwind } from '@remotion/tailwind-v4';

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.overrideWebpackConfig(enableTailwind);

// In sandboxed/cloud environments Remotion can't download its bundled
// Chromium. If a browser is provided via env var (e.g. a pre-installed
// Playwright Chromium), use it. On a normal machine these vars are unset
// and Remotion downloads/uses its own browser as usual.
if (process.env.REMOTION_BROWSER_EXECUTABLE) {
  Config.setBrowserExecutable(process.env.REMOTION_BROWSER_EXECUTABLE);
  // A full Chrome binary needs the new headless mode, not the old shell.
  Config.setChromeMode("chrome-for-testing");
}
