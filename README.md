
# Free Sleep (Local) — Home Assistant (HACS)

Custom integration to **pull local status** from a jailbroken Eight Sleep Pod running the **[free-sleep](https://github.com/throwaway31265/free-sleep)** server on your LAN.

> ⚠️ This talks to your Pod **entirely locally** (no cloud). The upstream project currently **does not implement authentication**, so **only expose it on a trusted LAN** and restrict WAN access at your router.

## What you get
- Sensors for heart rate, breath rate, HRV (if `biometrics` is enabled on free-sleep).
- Sensors for left/right temperature level, online status (when provided by `deviceStatus`).
- Binary sensors for left/right presence and heating/cooling activity (if available).
- All raw payloads attached as attributes for advanced automations.

## How it works
This integration polls the free-sleep REST API (e.g. `http://<pod-ip>:3000`) and merges data from a few known endpoints:

- `GET /api/deviceStatus` — general status (presence, temp levels, online).  
- `GET /api/settings` — configuration info.  
- `GET /api/schedules` — current schedules.  
- `GET /api/execute/state` — execution/job state (if present).  
- `GET /api/metrics/vitals` — latest biometrics sample(s) when biometrics is enabled.

> Note: The upstream API is evolving, so the integration uses **best‑effort keys** and tolerates missing fields. You can still access the full raw JSON on each entity via attributes.

## Install (HACS)
1. In HACS → **Integrations** → ⋮ → **Custom repositories**: add this zip/extracted folder as a custom repo (type: Integration).
2. Or copy `custom_components/free_sleep` into your Home Assistant `config/custom_components` directory.
3. Restart Home Assistant.
4. Settings → Devices & Services → **Add Integration** → search **Free Sleep (Local)** and enter your Pod IP (default port `3000`).

## Recommended upstream settings
- Make sure your pod is jailbroken and running **free-sleep** server. See upstream README for compatibility and install steps.  
- To enable biometrics (optional), run on the pod:
  ```sh
  sh /home/dac/free-sleep/scripts/enable_biometrics.sh
  ```

## Security
- Upstream warns there is **no auth** on the REST API. Block WAN access to the Pod and keep it on a **trusted LAN** only.

## Credits
- Upstream project: **free-sleep** by `throwaway31265`  
- This integration is community‑built and not affiliated with Eight Sleep.

