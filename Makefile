.PHONY: help test package regen-reference clean

help:
	@echo "Targets:"
	@echo "  make test              - Run mechanical test suite"
	@echo "  make package           - Build .skill bundle for distribution"
	@echo "  make regen-reference   - Refresh docs/slack-api/FULL-REFERENCE.md from Slack's OpenAPI spec"
	@echo "  make clean             - Remove generated artifacts"

test:
	python3 scripts/test_slack.py

package:
	python3 scripts/package_skill.py .
	@echo ""
	@echo "Install via: npx skills add <repo> -g -a claude-code -a gemini-cli -a codex -a pi -y"

regen-reference:
	python3 scripts/regen_reference.py docs/slack-api/FULL-REFERENCE.md

clean:
	rm -f slack-skill.skill
	find . -name __pycache__ -type d -exec rm -rf {} +
	find . -name '*.pyc' -delete
