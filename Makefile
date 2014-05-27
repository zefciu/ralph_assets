quicktest:
	DJANGO_SETTINGS_PROFILE=test-assets ralph test ralph_assets
	
test-with-coveralls:
	DJANGO_SETTINGS_PROFILE=test-assets coverage run --source=ralph_assets --omit='*migrations*' "$VIRTUAL_ENV/bin/ralph" test ralph_assets

flake:
	flake8 --exclude="migrations" --statistics src/ralph_assets

runserver:
	ralph runserver
