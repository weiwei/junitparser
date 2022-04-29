# Changelog

## [2.5.0] - 2022-03-14
### Added
- Bulk add test cases. Thanks to @Goblenus 
- 
## [2.4.3] - 2022-03-14
### Fixed
- Custom element not properly initiated according to the readme example.

## [2.4.2] - 2022-01-08
### Fixed
-  Fix the package build for a specific install method
## [2.4.1] - 2021-12-31
### Fixed
-  Parameter typo in the cli. Thanks to @petterssonandreas
-  
## [2.4.0] - 2021-12-30

This release addresses issues and PRs by @markgras. 
### Fixed
-  Parameter typo in function `write_xml()`.
- Properly closes file in `setup.py`.
### Enhancement
- Use generators in stead of lists in a few occasions.

## [2.3.0] - 2021-11-20
### Possibly Breaking
-  The time value now has a precision of 3 (#72). Thanks to @bryan-hunt.

## [2.2.0] - 2021-11-20
### Fixed
- Unescaping attribute values (#71).

## [2.1.1] - 2021-05-31
### Fixed
- CLI broken due to a quotation mark.

## [2.1.0] - 2021-05-30
### Fixed
- Should not have used default sys locale to parse numbers. Thanks to @EnricoMi

### Added
- Merge parameter enhancement: output to console if output file name is set to "-"
- Support testcase tags inside testcase tags. Thanks to @EnricoMi

## [2.0.0] - 2020-11-28
### Breaking
- `TestCase.result` is now a list instead of a single item. `Failure`, `Skip`, 
  etc. are all treated as results.

### Added
- `TestCase` constructor supports `time` and `classname` as params.
- `Result` object supports `text` attribute.
- Handles localized timestamps. Thanks to @ppalucha

## [1.6.3] - 2020-11-24
### Fixed
- `JunitXML.fromstring()` now handles various inputs.

## [1.6.2] - 2020-10-29
### Changed
- Exclude test file from package. Thanks to @Ishinomori

## [1.6.1] - 2020-10-29
### Changed
- Update licence and readme

## [1.6.0] - 2020-10-28
### Added
- Custom parser option for `fromfile`

## [1.5.1] - 2020-10-28
### Fixed
- #47 result error when running merge in cli

## [1.5.0] - 2020-10-26
### Added
- Runs with `python -m junitparser ...` Thanks to @jkowalleck
- `junitparser merge --glob` also by @jkowalleck

## [1.4.2] - 2020-10-21
### Fixed
- command line versioning

## [1.4.1] - 2019-12-26
### Fixed
- A conditional statement error. Thanks to @dries007

## [1.4.0] - 2019-10-28
### Fixed
- Retain suite name when merging test suites. Thanks to @alde
- Add skipped member to JUnitXml. Thanks to @arichardson

## [1.3.5] - 2019-09-23
### Fixed
- Prevented an exception when test result is None. Thanks to @patbro

## [1.3.4] - 2019-09-15
### Fixed
- Performance improvement for file merging. Thanks to @arichardson

## [1.3.3] - 2019-09-02
### Fixed 
- Ensure htmlentities are used in attributes. Thanks to @alde

## [1.3.1] - 2019-02-11
### Fixed
- Install with --no-binary

## [1.3.0] - 2019-02-11
### Fixed
- Merging test files doesn't merge test counts. Thanks to @andydawkins

## [1.2.0]
### Added
- Support for reading custom attributes and elements. Thanks to @arewm

## [1.1.0]
### Added
- a command to merge xml files. Thanks to @imsuwj

## [1.0.0]
### Added
- Python 2 support. Thanks to @SteinHeselmans

## [0.9.0]
### Changed
* Supports xmls with ``testcase`` as root node.
* First beta release.