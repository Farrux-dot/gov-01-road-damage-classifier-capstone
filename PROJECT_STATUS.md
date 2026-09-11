# Project Status

## Project

GOV-01 Road Damage Image Classifier

## Final assessed candidate

- Branch: `main`
- Final model: `mobilenetv2_frozen_v4`
- Task: one road image -> `Normal` or `Pothole` for human-review triage only.
- Final protected clean-test result: Macro F1 `0.939901`; accuracy `0.950820`; 183 images.
- Protected-test rule: the test result was recorded after model selection; no later tuning used the protected test set.

## Current stage

EXTC4 - Evidence and Defense Readiness Gate - **Yellow**

The project evidence, public demo route, local-demo evidence, and final defense deck are complete. The remaining personal preparation is to rehearse the presentation before submission or defense and record the real results honestly.

## Completed evidence

- Project scope and boundary are in `PROJECT_BRIEF.md` and `README.md`.
- V1 data audit, duplicate removal, clean split, preprocessing plan, and manifests are documented in `docs/`.
- Model-selection and protected-test evidence are in `reports/model_gate.md` and `reports/experiment_record.csv`.
- Error patterns and responsible-use boundaries are documented in `reports/error_analysis/ERROR_ANALYSIS.md` and `docs/RESPONSIBLE_AI_AND_LIMITATIONS.md`.
- The selected V1 model was saved, loaded in a fresh Colab runtime, and verified with the same proof-image probability (`0.907272`, difference `0.0`).
- The local Streamlit app ran successfully with the private model. Model-load, inference-test, and app-prediction screenshots are stored in `presentation/fallback_evidence/`.
- Local reproduction steps are in `docs/REPRODUCTION_TEST.md`.
- The final eight-slide defense deck is in `presentation/GOV_01_Road_Damage_Classifier_Defense.pptx`.

## Demo route

1. Primary route: public showcase -> [public Streamlit app](https://ff2050-gov01-road-damage.streamlit.app/) -> upload one new, non-protected road image -> **Classify image**.
2. Local verification route: run `python smoke_test.py --image <known-good-image>` and `python -m unittest discover -s tests -v` with the documented private local artifact.
3. Fallback route: show the real local evidence screenshots in `presentation/fallback_evidence/` and explain that raw data and the private local artifact are deliberately excluded from GitHub.

## V2 boundary

`experiment_dataset_v2_finetuning` is a separate experimental branch. Its protected-test result was weak, so it is closed and must not replace V1. The final assessed candidate remains V1 on `main`.

### Current V2 data-preparation experiment

- Active experimental branch: `codex/road-condition-v2`.
- PaveBench crack sample review completed on 2026-09-08: 36 images reviewed with seed `42`; 16 marked `clear_keep` and 20 marked `unclear_exclude`.
- PaveBench pothole/patch/negative sample review completed on 2026-09-08: 36 images reviewed with seed `42`; 17 marked `clear_keep` and 19 marked `unclear_exclude`.
- All 12 sampled PaveBench `pothole` images were excluded because no clear pothole was confirmed. Future V2 image-level pothole candidates will come from the 624 eligible V1 training images; V1 validation and protected-test images remain reserved.
- Eleven reviewed `patch` images remain candidates for `Repaired_road`; six reviewed `negative` images remain generic negative candidates and do not yet have specific road-condition labels.
- Data Gate decision: do not bulk-accept the PaveBench crack folders. Only individually reviewed clear images may remain candidates for a later V2 pool.
- PaveBench detection-label review completed on 2026-09-09 across 148 unique records from two review rounds. The combined evidence is documented in `docs/V2_PAVEBENCH_DETECTION_DATA_GATE.md` and `docs/v2_pavebench_detection_review_manifest.csv`.
- Detection-review results: Alligator 55/62 approved (88.7%); Crack 43/62 (69.4%); Patch 11/12 (91.7%); Pothole 4/12 (33.3%). These are human-review sample results, not model metrics or claims about every unreviewed image.
- Alligator may continue as a conditional `Crack` candidate. Crack must not be bulk-accepted. Only individually approved Patch records remain `Repaired_road` candidates. The PaveBench pothole class remains excluded; eligible V1 training pothole images remain the pothole source.
- The combined detection-review manifest contains 109 reviewed candidates and preserves two Round 1 evidence-quality flags without silently changing the original human decisions.
- No PaveBench image has been added to a combined V2 split and no V2 model has been trained from this review.
- The source-traceable pre-split candidate inventory was completed on 2026-09-09. It contains 6,733 records: 6,000 SVRDD source-training records, 624 eligible V1 training potholes, and 109 individually approved PaveBench detection records. See `docs/V2_CANDIDATE_INVENTORY.md` and `docs/v2_candidate_inventory.csv`.
- The inventory keeps all V1 validation/protected-test images and all SVRDD source validation/test images out of the candidate pool. It found zero exact SHA-256 duplicate groups across the 6,733 included records.
- Of the candidates, 6,109 have object boxes; the 624 V1 pothole images have image-level labels only and cannot support object detection without new box annotations.
- Important multi-class blocker: the provisional one-label priority rule produces only one primary `manhole_cover` image even though 1,688 candidate images contain a manhole label and 2,517 manhole boxes exist. Multi-class split construction is paused until this collapse is resolved honestly.
- A source-training-only manhole crop-review generator was completed on 2026-09-09. It found 2,517 manhole boxes, held 1,132 because the target was smaller than 12 pixels on its shortest side, held 679 because another labelled condition materially entered the crop, and left 706 candidates for visual review. See `docs/V2_MANHOLE_CROP_REVIEW_METHOD.md`.
- The deterministic 60-candidate review was completed on 2026-09-09. It contains 50 `approve_manhole` decisions and 10 `reject_unclear` decisions, with no pending, unsupported, or duplicate records. See `docs/v2_svrdd_manhole_crop_review_manifest.csv`.
- The reviewer reported difficulty identifying some targets because of the small source resolution. Of the 50 approvals, 24 have a target below 20 pixels and 15 are below 16 pixels. All approvals are therefore retained only as `retain_candidate_not_training_ready` and carry the `low_resolution_review_difficulty` evidence flag.
- Automated checks confirm that only `train.v2.jsonl` is accepted, region-balanced sampling is repeatable, and generated square crops remain inside image boundaries.
- A stricter Round 2 manhole review workbook was generated on 2026-09-09 from unused source-training candidates only. It excludes all 60 Round 1 candidate IDs, requires a target minimum side of 28 pixels, and contains 60 rows balanced at 12 per source region. Selected targets range from 28 to 57 pixels.
- The 28-pixel rule is evidence-based: it is the strongest tested cutoff that still supplies at least 12 unused eligible candidates in every region. At 32 pixels, Chaoyang has only six candidates.
- Round 2 human review was completed on 2026-09-09: 51 `approve_manhole`, 7 `reject_unclear`, and 2 `reject_not_manhole`, with no pending or unsupported decisions. Every rejected record has a reviewer note.
- The two SVRDD review rounds now provide 101 approved manhole crop candidates from 97 unique source images. Geometry and source traceability are preserved in `docs/v2_svrdd_manhole_approved_manifest.csv`.
- Four source images contribute two approved crops each. The approved manifest assigns one `split_group_id` per original image so related crops cannot be separated across future train, validation, and test sets.
- These 101 records are approved candidates, not a final V2 split. The 50 Round 1 approvals retain their low-resolution warning, and no V2 model has been trained from these records.
- The SVRDD repaired-road audit was completed on 2026-09-09 using source-training annotations only. The automatic prefilter found 5,089 repaired-road boxes: 2,685 clear-context candidates, 1,765 held because the target was smaller than 28 pixels, and 639 held because another labelled condition materially entered the contextual crop.
- Two repaired-road review rounds contain 100 unique candidates. Round 1 produced 51 `approve_repaired_road`, 7 `reject_unclear`, and 2 `wrong_box` decisions. The targeted Round 2 review produced 40 approvals from 20 additional Xicheng examples and 20 multi-patch box-completeness examples.
- The combined sample approval rate is 91%. This is review evidence, not a model metric and not proof that every unreviewed source annotation is correct.
- The audit retains 91 individually human-approved candidates and 2,585 unreviewed candidates marked honestly as `source_labeled_audit_supported`. It excludes 9 human-rejected candidates and continues to hold the 2,404 candidates that failed the automatic prefilter.
- The complete traceability record is documented in `docs/V2_REPAIRED_ROAD_REVIEW_METHOD.md` and the `docs/v2_svrdd_repaired_road_*_manifest.csv` files. Every record uses the original source image as its `split_group_id` to prevent future split leakage.
- All 2,676 retained repaired-road candidates were materialized as contextual RGB crops in the Git-ignored `data/processed/` workspace. The crops come from 1,513 source images and preserve exactly 1,513 source-based split groups. See `docs/V2_REPAIRED_ROAD_MATERIALIZATION.md` and `docs/v2_svrdd_repaired_road_materialization_manifest.csv`.
- File and geometry checks completed successfully: 2,676 manifest rows match 2,676 JPEG files, crop sides range from 128 to 1,024 pixels, and no source image or candidate record is missing.
- Exact SHA-256 checking found 23 duplicate crop groups containing 24 redundant crops beyond the first. Every duplicate remains inside one source image and one split group, so no cross-group leakage was found.
- Deterministic exact-content deduplication is complete: 2,652 unique records are retained and 24 redundant records are documented separately. No JPEG files were deleted. Human-approved evidence is preferred when choosing a keeper; otherwise candidate ID supplies a repeatable tie-break.
- The 60-row visual-quality review was completed on 2026-09-10. It used seed `42`, four crops from every region/size-band combination, and 60 unique original source images.
- Human review approved 51 repaired-road crops and rejected 9 unclear crops. The rejection reasons were one bus-shadow obstruction, three examples invisible to the human eye, and five examples where asphalt colour hid the repaired area.
- The final unique-quality evidence retains 2,643 candidates and excludes the 9 human-rejected unclear candidates. Of the retained candidates, 142 now have individual human approval and 2,501 remain honestly marked as source-labelled audit-supported candidates.
- See `docs/V2_REPAIRED_ROAD_DEDUPLICATION_AND_QUALITY_REVIEW.md`, `docs/v2_svrdd_repaired_road_unique_quality_review_manifest.csv`, `docs/v2_svrdd_repaired_road_unique_keep_manifest.csv`, and `docs/v2_svrdd_repaired_road_unique_quality_exclusions.csv`.
- No image files were deleted. No final V2 split has been created and no V2 model has been trained.
- Next small task: compare the retained candidate counts across all approved V2 classes and define the leakage-safe group split plan before creating any final combined split.

## EXTC4 evidence and defense readiness artifacts

- `docs/defense_pitch_outline.md` - complete five-minute route; personal timing remains pending.
- `docs/capstone_evidence_matrix.md` - all eight criteria, essential requirements, and three completed Show-Me-Where checks (all PASS on 2026-08-17).
- `docs/defense_question_bank.md` - ten likely questions with evidence references; personal live-answer record remains pending.
- `docs/final_action_plan.md` - exact final rehearsal actions and checks.

## Remaining finalization

1. Rehearse the final defense deck using `docs/defense_pitch_outline.md` and `presentation/SPEAKER_FLOW.md`; record actual duration and one revision.
2. Use `docs/defense_question_bank.md` and `presentation/Q_AND_A_BANK.md` to practise at least three questions and record one answer.
3. Debugging milestone completed (2026-08-15): added a Git-hygiene check and ignored the local `.venvv/` virtual-environment folder to prevent accidental commits. See `docs/AI_DEBUG_REPORT.md`.
4. After only final wording/layout corrections, freeze the repository state.
