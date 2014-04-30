quicktest:
	DJANGO_SETTINGS_PROFILE=test-assets ralph test ralph_assets

flake:
	flake8 --exclude="migrations" --statistics src/ralph_assets

runserver:
	ralph runserver
