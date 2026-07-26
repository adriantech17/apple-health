```yaml
schema: gentle-ai.remediation-result/v1
status: complete
failed_evidence_revision: sha256:9b67d95c234cec4a82ccd8ed21fd14bb82764495cd1d1643891135ea788c3133
lineage_id: review-6693164b990c28aa
generation: 1
fix_batch: 1
focused_tests: passed
runtime_harness: passed
rollback_boundary: recorded
```
```json
{"schema":"gentle-ai.remediation-evidence/v1","failed_evidence_revision":"sha256:9b67d95c234cec4a82ccd8ed21fd14bb82764495cd1d1643891135ea788c3133","lineage_id":"review-6693164b990c28aa","generation":1,"fix_batch":1,"commands":[{"command":".venv/bin/python -m pytest scripts/test_check_repository.py::RelocationManifestTests::test_archived_reclassification_requires_canonical_pass_verification","exit_code":0,"result":"1 focused archive verification test passed in 0.03s"},{"command":".venv/bin/python -m pytest","exit_code":0,"result":"68 project tests passed in 1.04s"},{"command":".venv/bin/python -m unittest scripts.test_check_repository","exit_code":0,"result":"22 repository policy tests passed in 0.097s"},{"command":"git diff --check","exit_code":0,"result":"No whitespace errors or conflict markers"}],"runtime_harness":{"status":"passed","command":".venv/bin/python scripts/check_repository.py","result":"Repository audit passed for 127 tracked files","na_reason":""},"rollback":{"boundary":"scripts/check_repository.py and scripts/test_check_repository.py","evidence":"Restore both files to remove only the canonical verification parser and its synthetic coverage"}}
```
