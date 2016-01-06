default:
	@echo "'make testredirects': test url redirects"

.PHONY: testredirects
testredirects:
	python ../tests/test_redirects.py './tests/test_redirects.json'
