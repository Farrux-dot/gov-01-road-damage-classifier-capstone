# V2 Hugging Face Manhole-Cover Source Audit

- **Source:** [delima87_manhole_covers_dataset](https://huggingface.co/datasets/delima87/manhole_covers_dataset)
- **Licence record:** Apache-2.0 stated on the dataset card; recheck before redistribution
- **Audit date:** 2026-09-19
- **Raw data changed:** No

## Verified results

- Readable images: 2726
- Source-train manhole candidates: 1197
- Held train-manhole exact duplicates: 0
- Reserved non-candidates: 1529
- Exact duplicate groups across supplied splits: 220

## Boundary

This is image-level manhole/void data. It supplies no bounding boxes, so it may support multi-class or multi-label lookalike learning only—not object detection. Only its official train/manhole images can enter the pre-split candidate inventory. Its void images and original validation/test images remain reserved. A final V2 split and visual sanity review are still required before training.
