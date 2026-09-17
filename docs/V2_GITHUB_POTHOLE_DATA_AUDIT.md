# V2 GitHub Pothole Dataset Audit

- **Source:** [jaygala24/pothole-detection](https://github.com/jaygala24/pothole-detection)
- **Licence:** MIT
- **Audit date:** 2026-09-17
- **Raw data changed:** No
- **Human visual decision:** Approved — potholes are clear.

## Verified results

- Images and matching labels: 1243 each
- Accepted unique images: 1241
- Accepted valid pothole boxes: 4061
- Exact duplicate groups: 2 (two redundant images excluded)
- Invalid source boxes: 1 (a zero-width box in `img-415.txt`; raw file preserved)

## Decision

This source is accepted as a **pothole-only detection candidate**. It must still be combined with other sources and split without leakage before model training. The source has no normal-road, shadow, manhole-cover, crack, or repaired-road labels.
