# Remotion video

<p align="center">
  <a href="https://github.com/remotion-dev/logo">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://github.com/remotion-dev/logo/raw/main/animated-logo-banner-dark.apng">
      <img alt="Animated Remotion Logo" src="https://github.com/remotion-dev/logo/raw/main/animated-logo-banner-light.gif">
    </picture>
  </a>
</p>

This project contains the **"i am josh dillard"** title animation
(`src/Composition.tsx`): the words spring in one by one over a blue→purple
gradient, with the name emphasized in bold white. It renders at
1920×1080, 30fps, 120 frames (4s) — configured in `src/Root.tsx`.

## Commands

**Install Dependencies**

```console
npm i
```

**Start Preview**

```console
npm run dev
```

**Render video** (writes `out/josh.mp4`)

```console
npm run render
```

### Rendering in a sandboxed / cloud environment

Some environments (e.g. Claude Code on the web) block Remotion from
downloading its bundled Chromium. If a browser is already present, point
Remotion at it with the `REMOTION_BROWSER_EXECUTABLE` env var — the config
in `remotion.config.ts` picks it up automatically and switches to the
required new-headless mode:

```console
REMOTION_BROWSER_EXECUTABLE=/path/to/chrome npm run render
```

For example, with a pre-installed Playwright Chromium:

```console
REMOTION_BROWSER_EXECUTABLE=$(ls -d /opt/pw-browsers/chromium-*/chrome-linux/chrome | head -1) npm run render
```

On a normal machine this var is unset and Remotion downloads/uses its own
browser as usual.

**Upgrade Remotion**

```console
npx remotion upgrade
```

## Docs

Get started with Remotion by reading the [fundamentals page](https://www.remotion.dev/docs/the-fundamentals).

## Help

We provide help on our [Discord server](https://discord.gg/6VzzNDwUwV).

## Issues

Found an issue with Remotion? [File an issue here](https://github.com/remotion-dev/remotion/issues/new).

## License

Note that for some entities a company license is needed. [Read the terms here](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md).
